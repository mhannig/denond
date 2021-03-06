#!/usr/bin/env python3

"""
Fake API
"""

from werkzeug.wrappers import Request, Response


class InvalidMethodError(Exception):
    pass

class EndpointNotFoundError(Exception):
    pass


class ApiDescription:

    def __init__(self):
        """Initialize the API description"""
        self.endpoints = {
            "GET": dict(),
            "POST": dict(),
            "PUT": dict(),
            "DELETE": dict(),
        }

    def add_endpoint(self,
                     method,
                     path,
                     content_type="application/json",
                     response=""):
        """
        Create an API endpoint

        An API endpoint is identified by a
        http method, a path and a response

        :param method: The HTTP Method (GET, POST, PUT, DELETE)
        :type method: str

        :param path: The request path /something/like/this
        :type path: str

        :param content_type: The response content type.
                             Default: application/json
        :type content_type: str

        :param response: The actual response
        :type response: str

        :return: returns instance of ApiDescription for chaining
        :rtype: ApiDescription
        """
        self.endpoints[method.upper()][path] = (response, content_type)

        return self


    def get_endpoint(self, method, path):
        """
        Return the content or raise a not found exception

        :param method: The HTTP method
        :type method: str

        :param path: The request path
        :type path: str

        :return: The content for the path and method
        :rtype: str
        """
        methods = self.endpoints.get(method.upper())
        if not methods:
            raise InvalidMethodError

        content = methods.get(path)
        if not content:
            raise EndpointNotFoundError

        return content


    def log_endpoints(self):
        """Show all registered endpoints"""
        for method, paths in self.endpoints.items():
            print(method + ":")
            for path in paths:
                print("   " + path)
            print("")

class FakeApiDescriptionLoader:

    def read(self, filename):
        """Load and parse a fake api description"""
        with open(filename) as f:
            return self._parse_file(f)

    def _parse_endpoint(self, line):
        """Checks if a line is an endpoint description"""
        tokens = line.split()
        if len(tokens) < 2:
            return None

        method = tokens[0]
        path = tokens[1]

        if len(tokens) == 3:
            content_type = tokens[2]
        else:
            content_type = "application/json"

        methods_available = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

        if method.upper() not in methods_available:
            return None # This is not an endpoint

        return (method, path, content_type)

    def _parse_file(self, lines):
        """Iterate over all lines and parse file"""
        api_description = ApiDescription()

        endpoint = None
        content = ""

        for line in lines:
            next_endpoint = self._parse_endpoint(line)

            # First endpoint
            if not endpoint and next_endpoint:
                endpoint = next_endpoint
                content = ""
                continue

            # Subsequent endpoints
            if next_endpoint and endpoint:
                # We have a new endpoint, just add
                # what we found in content to the api
                api_description.add_endpoint(*endpoint, content)

                # Read next endpoint
                endpoint = next_endpoint
                content = ""
                continue

            # Content
            if not next_endpoint:
                # Just add this to content
                content += line


        # Last endpoint:
        # We are done here, if there was a endpoint left,
        # add it to the api
        if endpoint:
            api_description.add_endpoint(*endpoint, content)

        return api_description


class FakeApi:

    def __init__(self, host="127.0.0.1", port=5000):
        """
        Initialize Fake API

        :param host: The listen host (default 127.0.0.1)
        :type host: str

        :param port: The listen port
        :type port: int
        """
        self.host = host
        self.port = port

        self.api_description = ApiDescription()

    def load(self, filename, loader=None):
        """
        Load API description from a file

        :param filename: The source filename
        :type filename: str
        """
        if not loader:
            # Use default loader
            loader = FakeApiDescriptionLoader()

        self.api_description = loader.read(filename)

    @Request.application
    def handle_request(self, request):
        """Handle the request and respond with content"""

        try:
            (content, content_type) = self.api_description \
                                          .get_endpoint(request.method,
                                                        request.path)
            return Response(content, content_type=content_type)
        except InvalidMethodError:
            return Response(status=405)
        except EndpointNotFoundError:
            return Response(status=404)


    def run_server(self):
        """
        Run a werkzeug WSGI server

        :return: Never returns
        """
        from werkzeug.serving import run_simple
        run_simple(self.host, self.port, self.handle_request)




if __name__ == "__main__":
    fake_api = FakeApi()
    fake_api.load("api.txt")
    fake_api.api_description.log_endpoints()
    fake_api.run_server()

