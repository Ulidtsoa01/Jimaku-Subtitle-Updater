from preset import *


def apply(confField):
  if confField in CONF and (CONF[confField] or CONF[confField] is 0):
    return True
  return False

