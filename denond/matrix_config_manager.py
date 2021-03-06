
"""
Audiomatrix configuration manager
"""
import time
import os

from glob import glob

import denon

from utils import Service

import matrix_config

class ConfigUploader(Service):
    """Handle Uploads"""
    def init(self, host):
        """Initialize service"""
        self.client = denon.Client(host)
        print("[i] Config uploader initialized")


    def handle_cast(self, action):
        """Just start the upload"""
        self.parent.cast(('UPLOAD_START', None))

        # Load config
        conf = matrix_config.MatrixConfig.from_file(action)
        try:
            self.client.write_matrix_config(conf)
        except Exception as e:
            self.parent.cast(('UPLOAD_ERROR', str(e)))
            return

        self.parent.cast(('UPLOAD_DONE', None))


    #
    # API
    #
    def upload(self, filename):
        self.cast(filename)


class ConfigManager(Service):
    """Manage audio matrix configurations"""

    def init(self, host, configs_path=None):
        """Initialize service"""
        if not configs_path:
            configs_path = os.path.join(os.path.dirname(__file__),
                                        '../mappings')

        self.host = host
        self.configs_path = configs_path

        # Uploader
        self.uploader = ConfigUploader(self).spawn(host)

        # State
        self.is_uploading = False
        self.upload_error = None


    def terminate(self):
        """Override default terminate to include child"""
        self.uploader.terminate()
        super(ConfigManager, self).terminate()


    def handle_call(self, action):
        """React to sync calls"""
        (request, payload) = action
        if request == 'LIST_CONFIGURATIONS':
            return self._fetch_configurations()
        elif request == 'GET_CURRENT_CONFIGURATIONS':
            return self._get_current_configuration()
        elif request == 'GET_UPLOAD_STATE':
            return self._get_upload_state()


    def handle_cast(self, action):
        """Async requests"""
        (request, payload) = action
        if request == 'UPLOAD_REQUEST':
            self.is_uploading = True
            self.upload_error = None
            self.uploader.upload(payload)
        elif request == 'UPLOAD_DONE':
            self.is_uploading = False
        elif request == 'UPLOAD_ERROR':
            self.is_uploading = False
            self.upload_error = payload


    def _get_upload_state(self):
        """Get current upload state"""
        return {
            'is_uploading': self.is_uploading,
            'error': self.upload_error,
        }


    def _fetch_configurations(self):
        """Get list of configs"""
        return glob(self.configs_path + '/*.yml')


    def _get_current_configuration(self):
        """Load all configs, compare to current"""

        all_configs = [(matrix_config.MatrixConfig.from_file(filename), filename)
                       for filename in self._fetch_configurations()]

        # Get current matrix settings
        client = denon.Client(self.host)
        current = client.read_matrix_config()

        for config, filename in all_configs:
            if current.diff(config).mapping == {}:
                return current, filename

        return (None, "unknown")


    #
    # API
    #
    def list_configurations(self):
        """Return list of available configurations"""
        return self.call(('LIST_CONFIGURATIONS', None))



    def get_current_matrix_config(self):
        """
        Read the audiomatrix config and find the corresponding
        audio matrix dump on disk
        """
        return self.call(('GET_CURRENT_CONFIGURATIONS', None))


    def upload(self, filename):
        if self.is_uploading:
            return 'is_uploading'
        self.cast(('UPLOAD_REQUEST', filename))
        return 'upload_requested'


    def get_upload_state(self):
        return self.call(('GET_UPLOAD_STATE', None))


