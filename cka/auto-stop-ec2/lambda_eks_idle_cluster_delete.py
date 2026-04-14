import boto3
import os
from datetime import datetime, timedelta, timezone
import json

def lambda_handler(event, context):
    """
    Delete EKS clusters with no Kubernetes API activity for 2 days
    Checks CloudTrail for AccessKubernetesApi events
    """
    
    eks = boto3.client('eks', region_name=os.environ.get('TARGET_REGION', 'ap-southeast-1'))
    cloudtrail = boto3.client('cloudtrail', region_name=os.environ.get('TARGET_REGION', 'ap-southeast-1'))
    
    # Configuration
    idle_days = event.get('idle_days', 3)  # Default 3 days of inactivity
    dry_run = event.get('dry_run', False)
    exclude_tagged = event.get('exclude_tagged', True)  # Skip if has KeepCluster tag
    
    results = {
        'deleted_clusters': [],
        'active_clusters': [],
        'skipped_clusters': [],
        'errors': []
    }
    
    # Calculate cutoff time
    cutoff_time = datetime.now(timezone.utc) - timedelta(days=idle_days)
    
    try:
        # List all EKS clusters
        clusters_response = eks.list_clusters()
        clusters = clusters_response.get('clusters', [])
        
        for cluster_name in clusters:
            try:
                # Describe cluster
                cluster_response = eks.describe_cluster(name=cluster_name)
                cluster = cluster_response['cluster']
                
                # Skip if cluster is not ACTIVE
                if cluster['status'] != 'ACTIVE':
                    continue
                
                created_at = cluster['createdAt']
                cluster_age_days = (datetime.now(timezone.utc) - created_at).days
                
                # Get tags
                tags = cluster.get('tags', {})
                
                cluster_info = {
                    'ClusterName': cluster_name,
                    'Status': cluster['status'],
                    'CreatedAt': created_at.isoformat(),
                    'AgeDays': cluster_age_days,
                    'Version': cluster.get('version'),
                    'Tags': tags
                }
                
                # Skip if has KeepCluster tag
                if exclude_tagged and tags.get('KeepCluster', '').lower() in ['true', 'yes']:
                    cluster_info['Reason'] = 'Has KeepCluster tag'
                    results['skipped_clusters'].append(cluster_info)
                    continue
                
                # Skip if cluster is too new (less than idle_days old)
                if cluster_age_days < idle_days:
                    cluster_info['Reason'] = f'Too new ({cluster_age_days} days old)'
                    results['active_clusters'].append(cluster_info)
                    continue
                
                # Check for recent Kubernetes API activity
                has_recent_activity = False
                last_activity = None
                
                # Look for AccessKubernetesApi events in CloudTrail
                try:
                    # Check for any EKS API calls related to this cluster
                    events_to_check = [
                        'AccessKubernetesApi',
                        'UpdateClusterConfig',
                        'UpdateClusterVersion',
                        'CreateNodegroup',
                        'UpdateNodegroupConfig',
                        'DeleteNodegroup'
                    ]
                    
                    for event_name in events_to_check:
                        lookup_response = cloudtrail.lookup_events(
                            LookupAttributes=[
                                {
                                    'AttributeKey': 'EventName',
                                    'AttributeValue': event_name
                                },
                            ],
                            StartTime=cutoff_time,
                            MaxResults=50
                        )
                        
                        for event in lookup_response.get('Events', []):
                            # Check if event is related to this cluster
                            cloud_trail_event = json.loads(event.get('CloudTrailEvent', '{}'))
                            request_params = cloud_trail_event.get('requestParameters', {})
                            
                            # Check if this event is for our cluster
                            if (cluster_name in str(request_params) or 
                                cluster_name == request_params.get('name') or
                                cluster_name == request_params.get('clusterName')):
                                
                                has_recent_activity = True
                                event_time = event.get('EventTime')
                                if not last_activity or event_time > last_activity:
                                    last_activity = event_time
                                break
                        
                        if has_recent_activity:
                            break
                    
                    # Also check for kubectl/API access via cluster endpoint
                    if not has_recent_activity:
                        # Check CloudWatch metrics for API server requests
                        cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get('TARGET_REGION', 'ap-southeast-1'))
                        
                        try:
                            metric_response = cloudwatch.get_metric_statistics(
                                Namespace='AWS/EKS',
                                MetricName='cluster_failed_node_count',  # Any metric to check if cluster is monitored
                                Dimensions=[
                                    {
                                        'Name': 'ClusterName',
                                        'Value': cluster_name
                                    }
                                ],
                                StartTime=cutoff_time,
                                EndTime=datetime.now(timezone.utc),
                                Period=86400,  # Daily
                                Statistics=['Average']
                            )
                            
                            # If we have recent metrics, cluster might be active
                            if metric_response.get('Datapoints'):
                                has_recent_activity = True
                                last_activity = max(dp['Timestamp'] for dp in metric_response['Datapoints'])
                        except:
                            pass
                    
                except Exception as e:
                    print(f"Error checking activity for {cluster_name}: {str(e)}")
                    # If we can't check activity, assume it's active (safety)
                    has_recent_activity = True
                
                cluster_info['HasRecentActivity'] = has_recent_activity
                if last_activity:
                    cluster_info['LastActivity'] = last_activity.isoformat()
                    cluster_info['DaysSinceActivity'] = (datetime.now(timezone.utc) - last_activity).days
                
                # Decide whether to delete
                if not has_recent_activity:
                    # Calculate approximate cost
                    hourly_cost = 0.10  # EKS cluster costs $0.10/hour
                    days_running = cluster_age_days
                    total_cost = hourly_cost * 24 * days_running
                    wasted_cost = hourly_cost * 24 * idle_days  # Cost while idle
                    
                    cluster_info['TotalCost'] = round(total_cost, 2)
                    cluster_info['WastedCost'] = round(wasted_cost, 2)
                    cluster_info['Reason'] = f'No activity for {idle_days} days'
                    
                    if not dry_run:
                        # First delete all nodegroups
                        try:
                            nodegroups_response = eks.list_nodegroups(clusterName=cluster_name)
                            nodegroups = nodegroups_response.get('nodegroups', [])
                            
                            for nodegroup_name in nodegroups:
                                try:
                                    eks.delete_nodegroup(
                                        clusterName=cluster_name,
                                        nodegroupName=nodegroup_name
                                    )
                                    cluster_info['DeletedNodegroups'] = cluster_info.get('DeletedNodegroups', [])
                                    cluster_info['DeletedNodegroups'].append(nodegroup_name)
                                except Exception as e:
                                    print(f"Error deleting nodegroup {nodegroup_name}: {str(e)}")
                            
                            # Then delete the cluster
                            eks.delete_cluster(name=cluster_name)
                            cluster_info['Action'] = 'DELETED'
                            
                        except Exception as e:
                            cluster_info['Error'] = str(e)
                            cluster_info['Action'] = 'DELETE_FAILED'
                            results['errors'].append(cluster_info)
                            continue
                    else:
                        cluster_info['Action'] = 'WOULD_DELETE'
                    
                    results['deleted_clusters'].append(cluster_info)
                else:
                    cluster_info['Reason'] = 'Has recent activity'
                    results['active_clusters'].append(cluster_info)
                    
            except Exception as e:
                results['errors'].append({
                    'ClusterName': cluster_name,
                    'Error': str(e)
                })
                
    except Exception as e:
        results['errors'].append({
            'Error': f'Failed to list clusters: {str(e)}'
        })
    
    # Calculate total savings
    total_saved = sum(c.get('WastedCost', 0) for c in results['deleted_clusters'])
    
    # Summary
    summary = {
        'DeletedCount': len(results['deleted_clusters']),
        'ActiveCount': len(results['active_clusters']),
        'SkippedCount': len(results['skipped_clusters']),
        'ErrorCount': len(results['errors']),
        'TotalSaved': f'${total_saved:.2f}',
        'IdleDays': idle_days,
        'DryRun': dry_run
    }
    
    # Log results
    if results['deleted_clusters']:
        print(f"{'Would delete' if dry_run else 'Deleted'} {len(results['deleted_clusters'])} idle clusters")
        for cluster in results['deleted_clusters']:
            print(f"  - {cluster['ClusterName']}: {cluster.get('Reason', 'No activity')}, Cost: ${cluster.get('WastedCost', 0):.2f}")
    
    message = f"{'DRY RUN: Would delete' if dry_run else 'Deleted'} {len(results['deleted_clusters'])} idle clusters (no activity for {idle_days} days), saved ${total_saved:.2f}"
    
    return {
        'statusCode': 200,
        'summary': summary,
        'results': results,
        'message': message
    }