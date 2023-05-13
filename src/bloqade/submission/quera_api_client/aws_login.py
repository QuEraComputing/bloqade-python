import os
from typing import Optional


def sso_login(profile: Optional[str] = None):
    """
    checks if aws has log-in, and performs attempt of sso login if not.
    by default profile should be set as env variable `AWS_PROFILE`,
    but can be specified as a parameter.
    """
    if profile is not None:
        os.environ["AWS_PROFILE"] = profile
    code = os.system("aws sts get-caller-identity ")
    if code != 0:
        print("login rsp code is " + str(code) + ". attempting to sso login:")
        os.system("aws sso login")
