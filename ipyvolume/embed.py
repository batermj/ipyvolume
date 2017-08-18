import os
import io
import zipfile
import shutil
from ipywidgets import embed as wembed
import ipyvolume
from ipyvolume.utils import download_to_file, download_to_bytes

html_template = u"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    {extra_script_head}
</head>
<body>
{body_pre}
{snippet}
{body_post}
</body>
</html>
"""


def save_ipyvolumejs(folderpath="", version=ipyvolume._version.__version_js__, devmode=False):
    """ output the ipyvolume javascript to a local file
    
    :type folderpath: str
    :type version: str
    :type devmode: bool

    """
    url = "https://unpkg.com/ipyvolume@{version}/dist/index.js".format(version=version)
    filename = 'ipyvolume.js'
    filepath = os.path.join(folderpath, filename)

    devfile = os.path.join(os.path.abspath(ipyvolume.__path__[0]), "..", "js", "dist", "index.js")
    if devmode and os.path.exists(devfile):
        if folderpath and not os.path.exists(folderpath):
            os.makedirs(folderpath)
        shutil.copy(devfile, filepath)
    else:
        download_to_file(url, filepath)
    directory = os.path.dirname(filepath)
    threejs = os.path.join(os.path.abspath(ipyvolume.__path__[0]), "static", "three.js")
    shutil.copy(threejs, directory)

    return "ipyvolume.js"


def save_requirejs(folderpath="", version="2.3.4"):
    """ download and save the require javascript to a local file

    :type folderpath: str
    :type version: str
    """
    url = "https://cdnjs.cloudflare.com/ajax/libs/require.js/{version}/require.min.js".format(version=version)
    filename = "require.min.v{0}.js".format(version)
    filepath = os.path.join(folderpath, filename)
    download_to_file(url, filepath)
    return filename


def save_embed_js(folderpath="", version=wembed.__html_manager_version__):
    """ download and save the ipywidgets embedding javascript to a local file

    :type folderpath: str
    :type version: str
    """
    url = u'https://unpkg.com/@jupyter-widgets/html-manager@{0:s}/dist/embed-amd.js'.format(version)
    filename = "embed-amd_v{0:s}.js".format(version[1:])
    filepath = os.path.join(folderpath, filename)

    download_to_file(url, filepath)
    return filename


def save_font_awesome(dirpath='', version="4.7.0"):
    """ download and save the font-awesome package to a local folder

    :type dirpath: str
    :type url: str

    """
    folder_name = "font-awesome-{0:s}".format(version)
    folder_path = os.path.join(dirpath, folder_name)
    if os.path.exists(folder_path):
        return folder_name

    url = "http://fontawesome.io/assets/font-awesome-{0:s}.zip".format(version)
    content, encoding = download_to_bytes(url)

    try:
        zip_folder = io.BytesIO(content)
        unzip = zipfile.ZipFile(zip_folder)
        top_level_name = unzip.namelist()[0]
        unzip.extractall(dirpath)
    except Exception as err:
        raise IOError('Could not unzip content from: {0}\n{1}'.format(url, err))

    os.rename(os.path.join(dirpath, top_level_name), folder_path)

    return folder_name


def embed_html(filepath, widgets, makedirs=True, title=u'IPyVolume Widget', all_states=False,
               offline=False, offline_req=True, scripts_path='scripts_folder',
               drop_defaults=False, template=html_template,
               template_options=(("extra_script_head", ""), ("body_pre", ""), ("body_post", "")),
               devmode=False):
    """ Write a minimal HTML file with widget views embedded.

    :type filepath: str
    :param filepath: The file to write the HTML output to.
    :type widgets: widget or collection of widgets or None
    :param widgets:The widgets to include views for. If None, all DOMWidgets are included (not just the displayed ones).
    :param makedirs: whether to make directories in the filename path, if they do not already exist
    :param title: title for the html page
    :param all_states: if True, the state of all widgets know to the widget manager is included, else only those in widgets
    :param offline: if True, use local urls for required js/css packages
    :param offline_req: if True and offline=True, download all js/css required packages,
    such that the html can be viewed with no internet connection
    :param scripts_path: the folder to save required js/css packages to (relative to the filepath)
    :type drop_defaults: bool
    :param drop_defaults: Whether to drop default values from the widget states
    :param template: template string for the html, must contain at least {title} and {snippet} place holders
    :param template_options: list or dict of additional template options
    :param devmode: if True, attempt to get index.js from local js/dist folder

    """
    dir_name_dst = os.path.dirname(os.path.abspath(filepath))
    if not os.path.exists(dir_name_dst) and makedirs:
        os.makedirs(dir_name_dst)

    template_opts = {"title": title, "extra_script_head": "", "body_pre": "", "body_post": ""}
    template_opts.update(dict(template_options))

    if all_states:
        state = None
    else:
        state = wembed.dependency_state(widgets, drop_defaults=drop_defaults)

    if not offline:
        # let ipywidgets deal with it
        wembed.embed_minimal_html(filepath, widgets, state=state,
                                                             requirejs=True, drop_defaults=drop_defaults)
        directory = os.path.dirname(filepath)
        threejs = os.path.join(os.path.abspath(ipyvolume.__path__[0]), "static", "three.js")
        shutil.copy(threejs, directory)
    else:
        if offline_req:
            if not os.path.isabs(scripts_path):
                scripts_path = os.path.join(os.path.dirname(filepath), scripts_path)
            # ensure script path is above filepath
            rel_script_path = os.path.relpath(scripts_path, os.path.dirname(filepath))
            if rel_script_path.startswith(".."):
                raise ValueError("The scripts_path must have the same root directory as the filepath")
            elif rel_script_path=='.':
                rel_script_path = ''
            else:
                rel_script_path += '/'

            #TODO would like to have ipyvolume.js in scripts_path (using require.config?)
            save_ipyvolumejs(dir_name_dst, devmode=devmode)
            fname_require = save_requirejs(os.path.join(scripts_path))
            fname_embed = save_embed_js(os.path.join(scripts_path))
            fname_fontawe = save_font_awesome(os.path.join(scripts_path))

        snippet = wembed.embed_snippet(widgets, embed_url=rel_script_path+fname_embed,
                                       requirejs=False, drop_defaults=drop_defaults, state=state)
        offline_snippet = """
<link href="{rel_script_path}{fname_fontawe}/css/font-awesome.min.css" rel="stylesheet">    
<script src="{rel_script_path}{fname_require}" crossorigin="anonymous"></script>
{snippet}
        """.format(rel_script_path=rel_script_path, fname_fontawe=fname_fontawe, fname_require=fname_require, snippet=snippet)

        template_opts['snippet'] = offline_snippet

        html_code = template.format(**template_opts)

        with io.open(filepath, "w", encoding='utf8') as f:
            f.write(html_code)
