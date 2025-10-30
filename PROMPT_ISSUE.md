I see! In the business_travel_prep.py file, ctx comes AFTER the parameters
  with defaults. The issue is that when using Field() for a required parameter,
  Python doesn't see it as having a default value. But Python's parser sees
  Field(description=...) as providing a default value to the parameter.

  The solution is to NOT use Field() for required parameters that come before
  ctx, or to put ctx at the end. Looking at the business_travel_prep example,
  ctx is at the end after all the optional parameters. Let me update my
  implementation to match that pattern:
