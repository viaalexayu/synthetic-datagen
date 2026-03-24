def read_file(filename):
    try:
        with open(filename, 'r') as f:
            while True:
                data = f.read()
                if not data:
                    break
                print (data)

    except Exception as e:
        print("Caught exception:", repr(e))
        
read_file("BGP Network dataset.csv")