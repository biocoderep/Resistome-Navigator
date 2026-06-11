import traceback
try:
    import backend.api.main
    print('Success!')
except Exception as e:
    traceback.print_exc()
