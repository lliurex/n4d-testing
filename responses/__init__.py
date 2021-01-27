
UNKNOWN_CLASS=-40
UNKNOWN_METHOD=-30
USER_NOT_ALLOWED=-20
AUTHENTICATION_FAILED=-10
INVALID_RESPONSE=-5
INVALID_ARGUMENTS=-3
UNHANDLED_ERROR=-2
CALL_FAILED=-1
CALL_SUCCESSFUL=0

HUMAN_RESPONSES={}
HUMAN_RESPONSES[UNKNOWN_CLASS]="Unknown class"
HUMAN_RESPONSES[UNKNOWN_METHOD]="Unknown method"
HUMAN_RESPONSES[USER_NOT_ALLOWED]="User not allowed"
HUMAN_RESPONSES[AUTHENTICATION_FAILED]="Authentication failed"
HUMAN_RESPONSES[INVALID_RESPONSE]="Invalid response"
HUMAN_RESPONSES[CALL_FAILED]="Call failed"
HUMAN_RESPONSES[UNHANDLED_ERROR]="Unhandled error"
HUMAN_RESPONSES[INVALID_ARGUMENTS]="Invalid arguments"
HUMAN_RESPONSES[CALL_SUCCESSFUL]="Call successful"

RESPONSE_FIELDS=["msg","status","return"]
VALID_STATUS=[UNKNOWN_CLASS,UNKNOWN_METHOD,USER_NOT_ALLOWED,USER_NOT_ALLOWED,AUTHENTICATION_FAILED,CALL_FAILED,CALL_SUCCESSFUL,INVALID_RESPONSE]

def is_valid_response(response):
	
	if not type(response)==dict:
		return False
	
	for field in RESPONSE_FIELDS:
		if field not in response:
			return False
			
	if response["status"] not in VALID_STATUS:
		return False
	
	return True
	
#def check_valid_response


def build_invalid_response(invalid_response):
	
	ret={}
	ret["msg"]=HUMAN_RESPONSES[INVALID_RESPONSE]
	ret["status"]=INVALID_RESPONSE
	ret["return"]=invalid_response
	
	return ret
	
#def build_invalid_response


def build_unknown_class_response():
	
	ret={}
	ret["msg"]=HUMAN_RESPONSES[UNKNOWN_CLASS]
	ret["status"]=UNKNOWN_CLASS
	ret["return"]=None
	
	return ret
	
#def build_response


def build_unknown_method_response():
	
	ret={}
	ret["msg"]=HUMAN_RESPONSES[UNKNOWN_METHOD]
	ret["status"]=UNKNOWN_METHOD
	ret["return"]=None
	
	return ret
	
#def build_response


def build_user_not_allowed_response():
	
	ret={}
	ret["msg"]=HUMAN_RESPONSES[USER_NOT_ALLOWED]
	ret["status"]=USER_NOT_ALLOWED
	ret["return"]=None
	
	return ret
	
#def build_response


def build_authentication_failed_response():
	
	ret={}
	ret["msg"]=HUMAN_RESPONSES[AUTHENTICATION_FAILED]
	ret["status"]=AUTHENTICATION_FAILED
	ret["return"]=None
	
	return ret
	
#def build_response

def build_invalid_arguments_response(ret_value,ret_msg=HUMAN_RESPONSES[INVALID_ARGUMENTS]):
	
	ret={}
	ret["msg"]=ret_msg
	ret["status"]=INVALID_ARGUMENTS
	ret["return"]=ret_value
	
	return ret

#def build_invalid_arguments_response


def build_failed_call_response(error_code=-1,ret_msg=HUMAN_RESPONSES[CALL_FAILED],tback_txt=""):
	
	ret={}
	ret["msg"]=ret_msg
	ret["status"]=CALL_FAILED
	ret["return"]=None
	ret["error_code"]=error_code
	ret["traceback"]=""
	
	return ret
	
#def build_response


def build_unhandled_error_response(ret_msg=HUMAN_RESPONSES[UNHANDLED_ERROR],tback_txt=""):
	
	ret={}
	ret["msg"]=ret_msg
	ret["status"]=UNHANDLED_ERROR
	ret["return"]=None
	ret["traceback"]=tback_txt
	
	return ret
	
#def build_response


def build_successful_call_response(ret_value=True,ret_msg=HUMAN_RESPONSES[CALL_SUCCESSFUL],status_code=0):
	
	ret={}
	ret["msg"]=ret_msg
	ret["status"]=CALL_SUCCESSFUL
	ret["return"]=ret_value
	ret["status_code"]=status_code
	
	return ret
	
#def build_response