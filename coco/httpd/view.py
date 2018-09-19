# -*- coding: utf-8 -*-
#

from flask import render_template, request, jsonify

from .app import app
from .elfinder import connector, volumes
from ..models import Connection
from ..sftp import InternalSFTPClient
from .auth import login_required
from .utils import get_cache_volume, set_cache_volume
from ..service import app_service


@app.route('/coco/elfinder/sftp/connector/<host>/', methods=['GET', 'POST'])
@login_required
def sftp_host_connector_view(host):
    sid = request.args.get("sid") or request.values.get('sid')
    print("Get sid: {}".format(sid))
    volume = None
    if sid:
        volume = get_cache_volume(sid)
    if not volume:
        print("New volume")
        user = request.current_user
        connection = Connection(addr=(request.real_ip, 0))
        connection.user = user
        sftp = InternalSFTPClient(connection)
        volume = volumes.SFTPVolume(sftp)
        set_cache_volume(sid, volume)
        if host != '_':
            asset = app_service.get_asset(host)
            if not asset:
                return jsonify({'error': 'Not found this host'})
            hostname = asset.hostname
            if asset.org_id:
                hostname = "{}.{}".format(asset.hostname, asset.org_name)
            volume.root_name = hostname
            volume.base_path = '/' + hostname

    handler = connector.ElFinderConnector([volume])
    handler.run(request)

    # If download file, return a view response
    if handler.return_view:
        return handler.return_view
    if handler.headers['Content-type'] == 'application/json':
        return jsonify(handler.response)


@app.route('/coco/elfinder/sftp/<host>/')
def sftp_host_finder(host):
    return render_template('elfinder/file_manager.html', host=host)


@app.route('/coco/elfinder/sftp/')
def sftp_finder():
    return render_template('elfinder/file_manager.html', host='_')


