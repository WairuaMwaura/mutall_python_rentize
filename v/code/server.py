#
# Import the uvicorn server that will run my API (FastAPI app) to the browser or
#   external clients.
import uvicorn
#
# Check if file is ran directly NOT imported????????
if __name__ == "__main__":
    #
    # Configure the uvicorn server to run with the following options.
    uvicorn.run(
        #
        # Load the 'my_app' FastAPI object from 'app.py' file.
        "app:my_app",
        #
        # Configure server to listen for network connections only on the
        #   specified address of a machine's network interface.
        host="127.0.0.1",
        #
        # Configure server to listen to a specific port on that 'host' above.
        port=8001,
        #
        # Restart the server automatically when I change my code.
        reload=True,
        #
        # Watch current folder for changes.
        reload_dirs=["./"],
        #
        # Include specific file patterns.
        reload_includes = ["*.py"],
        #
        # Exclude unnecessary files.
        reload_excludes = ["*.pyc", "__pycache__/*"]
    )