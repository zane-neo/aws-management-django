from django.test import TestCase

# Create your tests here.

import os

res = os.listdir('/Users/zaniu/Documents/code/ml-commons/plugin/build/distributions')
print(type(res))
print(res)