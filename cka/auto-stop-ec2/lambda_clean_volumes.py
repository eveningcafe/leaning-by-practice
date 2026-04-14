import boto3
import os
from datetime import datetime, timedelta, timezone

def lambda_handler(event, context):
    """
    Auto-delete unattached EBS volumes based on age and tags
    """
    
    ec2 = boto3.client('ec2', region_name=os.environ.get('TARGET_REGION', 'ap-southeast-1'))
    
    # Configuration from event or defaults
    days_unattached = event.get('days_unattached', 7)  # Delete volumes unattached for > 7 days
    dry_run = event.get('dry_run', False)  # Set to True to test without deleting
    exclude_tagged = event.get('exclude_tagged', True)  # Skip volumes with "KeepVolume" tag
    
    # Get all available (unattached) volumes
    response = ec2.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )
    
    volumes_to_delete = []
    volumes_skipped = []
    total_size_gb = 0
    
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_unattached)
    
    for volume in response['Volumes']:
        volume_id = volume['VolumeId']
        created_time = volume['CreateTime']
        size_gb = volume['Size']
        
        # Get tags
        tags = {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
        volume_name = tags.get('Name', 'Unnamed')
        
        # Skip if has KeepVolume tag
        if exclude_tagged and tags.get('KeepVolume', '').lower() in ['true', 'yes']:
            volumes_skipped.append({
                'VolumeId': volume_id,
                'Name': volume_name,
                'Reason': 'Has KeepVolume tag',
                'Size': size_gb
            })
            continue
        
        # Skip if volume is a snapshot source that's still needed
        if tags.get('SnapshotSource', '').lower() in ['true', 'yes']:
            volumes_skipped.append({
                'VolumeId': volume_id,
                'Name': volume_name,
                'Reason': 'Marked as snapshot source',
                'Size': size_gb
            })
            continue
        
        # Check if volume has been unattached long enough
        if created_time < cutoff_date:
            # Additional check: See when it was last attached
            # Look for state transition in CloudTrail or use creation time as proxy
            
            days_unattached_actual = (datetime.now(timezone.utc) - created_time).days
            
            volumes_to_delete.append({
                'VolumeId': volume_id,
                'Name': volume_name,
                'Size': size_gb,
                'CreatedTime': created_time.isoformat(),
                'DaysUnattached': days_unattached_actual,
                'EstimatedMonthlyCost': round(size_gb * 0.10, 2)  # $0.10 per GB per month
            })
            total_size_gb += size_gb
    
    # Calculate cost savings
    monthly_savings = total_size_gb * 0.10  # $0.10 per GB per month for gp3
    
    # Delete or report volumes
    deleted_volumes = []
    failed_deletions = []
    
    if volumes_to_delete and not dry_run:
        for vol in volumes_to_delete:
            try:
                # Create snapshot before deletion (optional safety measure)
                if event.get('create_snapshot_before_delete', False):
                    snapshot_response = ec2.create_snapshot(
                        VolumeId=vol['VolumeId'],
                        Description=f"Auto-snapshot before deletion of {vol['Name']} ({vol['VolumeId']})",
                        TagSpecifications=[
                            {
                                'ResourceType': 'snapshot',
                                'Tags': [
                                    {'Key': 'Name', 'Value': f"auto-snap-{vol['Name']}"},
                                    {'Key': 'AutoCreated', 'Value': 'true'},
                                    {'Key': 'SourceVolumeId', 'Value': vol['VolumeId']},
                                    {'Key': 'DeletionDate', 'Value': datetime.now(timezone.utc).isoformat()}
                                ]
                            }
                        ]
                    )
                    vol['SnapshotId'] = snapshot_response['SnapshotId']
                
                # Delete the volume
                ec2.delete_volume(VolumeId=vol['VolumeId'])
                deleted_volumes.append(vol)
                
            except Exception as e:
                failed_deletions.append({
                    'VolumeId': vol['VolumeId'],
                    'Error': str(e)
                })
    
    # Prepare response
    result = {
        'statusCode': 200,
        'summary': {
            'volumes_found': len(volumes_to_delete),
            'volumes_deleted': len(deleted_volumes),
            'volumes_skipped': len(volumes_skipped),
            'total_size_gb': total_size_gb,
            'estimated_monthly_savings': f'${monthly_savings:.2f}',
            'dry_run': dry_run
        },
        'deleted_volumes': deleted_volumes,
        'skipped_volumes': volumes_skipped,
        'failed_deletions': failed_deletions
    }
    
    # Log to CloudWatch
    if deleted_volumes:
        print(f"Deleted {len(deleted_volumes)} volumes, saving ${monthly_savings:.2f}/month")
        for vol in deleted_volumes:
            print(f"  - {vol['Name']} ({vol['VolumeId']}): {vol['Size']}GB, {vol['DaysUnattached']} days old")
    
    if dry_run:
        result['message'] = f"DRY RUN: Would delete {len(volumes_to_delete)} volumes saving ${monthly_savings:.2f}/month"
    else:
        result['message'] = f"Deleted {len(deleted_volumes)} volumes saving ${monthly_savings:.2f}/month"
    
    return result