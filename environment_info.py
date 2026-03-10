
# environment_info.py
# Reads the current log file index from a fixed index file on disk.
# Returns the index as an integer, or 65535 as a replacement value if anything goes wrong.

def getLogFileNumber():
    # Reads the first word from the log index file and returns it as an integer.
    # If the file is missing, empty, or its content is not a valid number,
    # the error replacement value 65535 is returned instead.

    # Default return value used as a replacement for errors (0xFFFF = 65535)
    nCurrentLogIndex = 65535
    filepath = "/home/debian/myprogs/DiDeBoCCS/logs/logindex"

    try:
        with open(filepath, "r") as f:
            # Read the file and split into words
            content = f.read().split()
            if content:
                # Take the first word as the log index string
                strCurrentLogIndex = content[0]
                # print("Ok, found currentLogIndex " + strCurrentLogIndex)
            else:
                print("No logindex found, file " + filepath + " is empty.")
    except FileNotFoundError:
        print(f"No logindex found, because file not found: {filepath}")

    try:
        # Convert the string log index to an integer
        nCurrentLogIndex = int(strCurrentLogIndex)
    except:
        # If conversion fails (non-numeric value or variable never set), log it and keep the error replacement value
        print("logindex is no number: " + strCurrentLogIndex + ". Ignoring it.")

    return nCurrentLogIndex

if __name__ == "__main__":
    # Entry point for standalone testing
    print("Testing environment_info...")
    print("log index is " + str(getLogFileNumber()))