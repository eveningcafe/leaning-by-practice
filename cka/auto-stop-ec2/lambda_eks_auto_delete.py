import boto3
import os
from datetime import datetime, timedelta, timezone
import json

def lambda_handler(event, context):
    """
    Auto-delete EKS nodegroups running longer than 3 hours
    """
    
    eks = boto3.client('eks', region_name=os.environ.get('TARGET_REGION', 'ap-southeast-1'))
    
    # Configuration
    max_hours = event.get('max_hours', 3)  # Default 3 hours
    dry_run = event.get('dry_run', False)
    exclude_tagged = event.get('exclude_tagged', True)  # Skip if has KeepNodegroup tag
    
    results = {
        'deleted_nodegroups': [],
        'skipped_nodegroups': [],
        'active_nodegroups': [],
        'errors': []
    }
    
    try:
        # List all EKS clusters
        clusters_response = eks.list_clusters()
        clusters = clusters_response.get('clusters', [])
        
        for cluster_name in clusters:
            try:
                # List nodegroups for each cluster
                nodegroups_response = eks.list_nodegroups(clusterName=cluster_name)
                nodegroups = nodegroups_response.get('nodegroups', [])
                
                for nodegroup_name in nodegroups:
                    try:
                        # Describe nodegroup
                        ng_response = eks.describe_nodegroup(
                            clusterName=cluster_name,
                            nodegroupName=nodegroup_name
                        )
                        nodegroup = ng_response['nodegroup']
                        
                        # Skip if not ACTIVE (already deleting or creating)
                        if nodegroup['status'] != 'ACTIVE':
                            continue
                        
                        # Check creation time
                        created_at = nodegroup['createdAt']
                        hours_running = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
                        
                        # Get tags
                        tags = nodegroup.get('tags', {})
                        
                        # Get instance details
                        instance_types = nodegroup.get('instanceTypes', [])
                        scaling_config = nodegroup.get('scalingConfig', {})
                        desired_size = scaling_config.get('desiredSize', 0)
                        
                        nodegroup_info = {
                            'ClusterName': cluster_name,
                            'NodegroupName': nodegroup_name,
                            'InstanceTypes': instance_types,
                            'DesiredSize': desired_size,
                            'HoursRunning': round(hours_running, 2),
                            'CreatedAt': created_at.isoformat(),
                            'Tags': tags
                        }
                        
                        # Skip if has KeepNodegroup tag
                        if exclude_tagged and tags.get('KeepNodegroup', '').lower() in ['true', 'yes']:
                            nodegroup_info['Reason'] = 'Has KeepNodegroup tag'
                            results['skipped_nodegroups'].append(nodegroup_info)
                            continue
                        
                        # Check if should delete (running too long)
                        if hours_running > max_hours:
                            # Calculate cost impact
                            instance_costs = {
                                't3.nano': 0.0052,
                                't3.micro': 0.0104,
                                't3.small': 0.0208,
                                't3.medium': 0.0416,
                                't3.large': 0.0832,
                                't3.xlarge': 0.1664,
                                't3.2xlarge': 0.3328
                            }
                            
                            hourly_cost = 0
                            for itype in instance_types:
                                hourly_cost += instance_costs.get(itype, 0.05) * desired_size
                            
                            nodegroup_info['HourlyCost'] = round(hourly_cost, 2)
                            nodegroup_info['WastedCost'] = round(hourly_cost * (hours_running - max_hours), 2)
                            
                            if not dry_run:
                                # Delete the nodegroup
                                try:
                                    eks.delete_nodegroup(
                                        clusterName=cluster_name,
                                        nodegroupName=nodegroup_name
                                    )
                                    nodegroup_info['Status'] = 'DELETING'
                                    results['deleted_nodegroups'].append(nodegroup_info)
                                    
                                    print(f"Deleted nodegroup {cluster_name}/{nodegroup_name} - running {hours_running:.1f} hours")
                                    
                                except Exception as e:
                                    nodegroup_info['Error'] = str(e)
                                    results['errors'].append(nodegroup_info)
                            else:
                                nodegroup_info['Status'] = 'WOULD_DELETE'
                                results['deleted_nodegroups'].append(nodegroup_info)
                        else:
                            results['active_nodegroups'].append(nodegroup_info)
                            
                    except Exception as e:
                        results['errors'].append({
                            'Nodegroup': f'{cluster_name}/{nodegroup_name}',
                            'Error': str(e)
                        })
                        
            except Exception as e:
                # Skip if cluster has no nodegroups or access denied
                if 'ResourceNotFoundException' not in str(e):
                    results['errors'].append({
                        'Cluster': cluster_name,
                        'Error': str(e)
                    })
                
    except Exception as e:
        results['errors'].append({
            'Error': f'Failed to list clusters: {str(e)}'
        })
    
    # Calculate total savings
    total_saved = sum(ng.get('WastedCost', 0) for ng in results['deleted_nodegroups'])
    
    # Summary
    summary = {
        'DeletedCount': len(results['deleted_nodegroups']),
        'SkippedCount': len(results['skipped_nodegroups']),
        'ActiveCount': len(results['active_nodegroups']),
        'ErrorCount': len(results['errors']),
        'TotalSaved': f'${total_saved:.2f}',
        'MaxHours': max_hours,
        'DryRun': dry_run
    }
    
    message = f"{'DRY RUN: Would delete' if dry_run else 'Deleted'} {len(results['deleted_nodegroups'])} nodegroups (>{max_hours}h), saved ${total_saved:.2f}"
    
    return {
        'statusCode': 200,
        'summary': summary,
        'results': results,
        'message': message
    }