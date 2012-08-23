import os
from os import path
from merge import FileHunk

from exceptions import ExternalAssetsError

try:
    # Current version of glob2 does not let us access has_magic :/
    import glob2 as glob
    from glob import has_magic
except ImportError:
    import glob
    from glob import has_magic

__all__ = ('ExternalAssets',)

class ExternalAssets(object):

    def __init__(self, folders):

        self.folders = folders
        self.debug = None
        self.seps = ('?','#')

    def get_versioned_file(self, file_name):
        suffix = None
        for sep in self.seps:
            if sep in file_name:
                parts = list(self.rpartition_file_name(file_name, sep))
                parts.pop(0)
                suffix = ''.join(parts)
        version = self.get_version(file_name)
        bits = file_name.split('.')
        bits.insert(len(bits)-1, version)
        versioned = '.'.join(bits)
        return versioned

    def versioned_folder(self, file_name):
        output_folder = self.env.config.get('external_assets_output_folder', None)
        if output_folder is None:
            raise ExternalAssetsError('You must set the external_assets_output_folder config value')
        try:
            versioned = self.get_versioned_file(file_name)
            return path.join(output_folder, path.basename(versioned))
        except IOError:
            return file_name

    def get_output_path(self, file_name):
        file_name = self.clean_file_name(file_name)
        return self.env.abspath(self.versioned_folder(file_name))

    def write_file(self, file_name):
        clean_file_name = self.clean_file_name(file_name)
        output_path = self.get_output_path(clean_file_name)
        hunk = FileHunk(self.env.abspath(clean_file_name))
        output_dir = path.dirname(output_path)
        if not path.exists(output_dir):
            os.makedirs(output_dir)
        hunk.save(output_path)
        if self.env.manifest:
            self.env.manifest.remember_file(file_name, self.env, self.get_version(file_name))

    def write_files(self):
        for folder in self.folders:
            path = self.env.abspath(folder)
            for file_name in glob.glob(path):
                self.write_file(file_name.replace('%s/' % self.env.abspath(''),''))

    def show_manifest(self):
        if self.env.manifest:
            print self.env.manifest.get_manifest()

    def url(self, file_name):
        file_name = self.clean_file_name(file_name)
        # resolve debug
        debug = self.debug if self.debug is not None else self.env.debug
        if debug:
            # we just need to return the absolute url
            url = self.env.absurl(file_name)
        else:
            versioned = self.versioned_folder(file_name)
            url = self.env.absurl(versioned)
            if not path.exists(self.env.abspath(versioned)):
                self.write_file(file_name)
        return url

    def rpartition_file_name(self, file_name, sep):
        return file_name.rpartition(sep)

    def clean_file_name(self, file_name):
        for sep in self.seps:
            if sep in file_name:
                return self.rpartition_file_name(file_name, sep)[0]
        return file_name

    def get_version(self, file_name):
        file_name = self.clean_file_name(file_name)
        version = None
        if self.env.manifest:
            version = self.env.manifest.query_file(file_name, self.env)
        if version is None:
            version = self.env.versions.determine_file_version(file_name, self.env)
        return version