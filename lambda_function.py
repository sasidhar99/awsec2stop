#Shutdown Ec2 instances using AWS Lambda and python code
#This Python code will shutdown running or pending ec2 instances in that region 

#import the aws library boto3
import boto3
regions_list=[] #provide the required regions e.g. ['region1','region2'] or [] for all regions.
#function to extract list of tags for a instance 
def get_tags(tag_list):
	tag_dict={}
	if tag_list is None:
	    return None
	else:
	    for tag in tag_list:
		    tag_dict.update({tag['Key'].upper():tag['Value'].upper()})
	    return(tag_dict)

def Get_Running_Instances(region):
    """
    function to get ec2 instances that are in state Running or pending
    and return a list with all the instances id
    """
    ec2 = boto3.resource('ec2', region_name=region)
    #call the features resource from the boto3 library
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    #filter the instances returned using the state name
    stop_list=[]
    for instance in instances:
        tags=get_tags(instance.tags)
        if tags is None:
            stop_list.append(instance.id)
        else:
            """
            enter all the tags in the below condition in uppercase only, 
            irrespective of the case of the tags attached to the EC2 instances on the AWS console.
            """
            if('AVIATRIX' in tags.values()):
                continue
            elif('NAME' not in tags.keys() or 'OWNER' not in tags.keys()):
                stop_list.append(instance.id)
            elif(len(tags['NAME' or 'OWNER' or 'COST-CENTER'])==0):
                stop_list.append(instance.id)
            elif('COST-CENTER' not in tags.keys() or tags['COST-CENTER']!='SLBDEV'):
                stop_list.append(instance.id)
 
    return (stop_list)
    #return a list with the ids of the instances
    
def Stop_Instances(region):
    #gets the instance ids to stop
    ids=Get_Running_Instances(region)
    """
    shutdown the Ec2 instances that has been returned by the function Get_Running_Instances
    """
    ec2 = boto3.client('ec2' , region_name=region)
    #call the features client from the boto3 library
    if not ids:
        #if the list of Ec2 instances returned is empty.
        print("No Instance in the state Running or pending in {} ".format(region))
    else:
        #tag the instances with 'Terminate Instance' before stopping
        ec2.create_tags(
            Resources=ids,
            Tags=[
                {
                    'Key': 'Terminate Instance',
                    'Value': 'True'
                    
                },
            ]
        )
        ec2.stop_instances(InstanceIds=ids)
        #stop the instances using their id
        ec2.get_waiter('instance_stopped').wait(InstanceIds=ids)
        #wait for the state of the instances to change to stopped.
        
        print ("Stopped and tagged for terminate {} instances in {} region".format(ids, region))
     
def lambda_handler(event, context):
    """
    launch the function Stop_Instances() in the lambda function 
    Handler for the Lambda function "lambda_function.lambda_handler"
    Timeout need to be more than 1 minute, so that our function can run perfectly 
    if you have an important number of instances to be shutdown, change the parameter of timeout
    """
    ec2 = boto3.client('ec2')
    if not regions_list:
        regions = ec2.describe_regions().get('Regions',[])
        for each_region in regions:
            Stop_Instances(each_region['RegionName'])
    else:
        for each_region in regions_list:
            Stop_Instances(each_region)
