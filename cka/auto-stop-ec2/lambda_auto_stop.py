import boto3
import os
from datetime import datetime, timezone

def lambda_handler(event, context):
    """
    Auto-stop EC2 instances based on tags or running time
    """
    
    ec2 = boto3.client('ec2', region_name=os.environ.get('TARGET_REGION', 'ap-southeast-1'))
    
    # Get instances to stop based on different criteria
    filters = []
    
    # Method 1: Stop instances with specific tag
    if event.get('stop_by_tag'):
        filters.append({
            'Name': 'tag:AutoStop',
            'Values': ['true', 'True', 'yes', 'Yes']
        })
    
    # Method 2: Stop all instances except those with KeepRunning tag
    if event.get('stop_all_except_tagged'):
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']},
                {'Name': 'tag:KeepRunning', 'Values': ['false', 'False', 'no', 'No']}
            ]
        )
    else:
        response = ec2.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ] + filters
        )
    
    instances_to_stop = []
    stopped_instances = []
    
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            
            # Method 3: Stop instances running longer than X hours
            if event.get('max_running_hours'):
                launch_time = instance['LaunchTime']
                running_hours = (datetime.now(launch_time.tzinfo) - launch_time).total_seconds() / 3600
                
                if running_hours > event['max_running_hours']:
                    instances_to_stop.append(instance_id)
                    instance_name = [tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name']
                    stopped_instances.append({
                        'InstanceId': instance_id,
                        'Name': instance_name[0] if instance_name else 'N/A',
                        'RunningHours': round(running_hours, 2)
                    })
            
            # Method 4: Stop specific student instances after hours
            elif event.get('stop_pattern'):
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                if 'Name' in tags and event['stop_pattern'] in tags['Name']:
                    instances_to_stop.append(instance_id)
                    stopped_instances.append({
                        'InstanceId': instance_id,
                        'Name': tags.get('Name', 'N/A')
                    })
            
            # Default: stop if has AutoStop tag
            else:
                tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                if tags.get('AutoStop', '').lower() in ['true', 'yes']:
                    instances_to_stop.append(instance_id)
                    stopped_instances.append({
                        'InstanceId': instance_id,
                        'Name': tags.get('Name', 'N/A')
                    })
    
    # Stop the instances
    if instances_to_stop:
        ec2.stop_instances(InstanceIds=instances_to_stop)
        
        return {
            'statusCode': 200,
            'body': {
                'message': f'Successfully stopped {len(instances_to_stop)} instances',
                'stopped_instances': stopped_instances
            }
        }
    else:
        return {
            'statusCode': 200,
            'body': {
                'message': 'No instances to stop',
                'stopped_instances': []
            }
        }