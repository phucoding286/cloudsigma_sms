import os
import sys

platform = sys.platform

if platform.startswith("win"):
    os.system("python ./cloudsigma_sms/cloudsigma_sms.py")
else:
    os.system("python3 ./cloudsigma_sms/cloudsigma_sms.py")