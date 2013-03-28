from couchpotato import get_session
from couchpotato.api import addApiView
from couchpotato.core.event import fireEvent, addEvent
from couchpotato.core.helpers.encoding import ss, toUnicode
from couchpotato.core.helpers.request import getParam, jsonified
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from couchpotato.core.plugins.scanner.main import Scanner
from couchpotato.core.settings.model import File, Release as Relea, Movie, ReleaseInfo
from sqlalchemy.sql.expression import and_, or_
import os
import random
log = CPLog(__name__)


class Release(Plugin):

    def __init__(self):
        addEvent('release.add', self.add)

        addApiView('release.add2', self.add2, docs = {
            'desc': 'Add a release manually to a movie',
            'params': {
                'lib_id': {'type': 'id', 'desc': 'ID of the Library in library-table'},
                'qua_id': {'type': 'id', 'desc': 'ID of the Quality in quality-table'},
                'name': {'type': 'string', 'desc': 'Name of the NZB file'}
            }
        })
        addApiView('release.download', self.download, docs = {
            'desc': 'Send a release manually to the downloaders',
            'params': {
                'id': {'type': 'id', 'desc': 'ID of the release object in release-table'}
            }
        })
        addApiView('release.delete', self.deleteView, docs = {
            'desc': 'Delete releases',
            'params': {
                'id': {'type': 'id', 'desc': 'ID of the release object in release-table'}
            }
        })
        addApiView('release.status', self.statusView, docs = {
            'desc': 'Change the status of release',
            'params': {
                'id': {'type': 'id', 'desc': 'ID of the release object in release-table'},
                'status': {'type': 'string: done, available, snatched, deleted', 'desc': 'New status for the release'}
            }
        })
        addApiView('release.ignore', self.ignore, docs = {
            'desc': 'Toggle ignore, for bad or wrong releases',
            'params': {
                'id': {'type': 'id', 'desc': 'ID of the release object in release-table'}
            }
        })

        addEvent('release.delete', self.delete)
        addEvent('release.status', self.status)
        addEvent('release.clean', self.clean)

    def add(self, group):
        db = get_session()

        identifier = '%s.%s.%s' % (group['library']['identifier'], group['meta_data'].get('audio', 'unknown'), group['meta_data']['quality']['identifier'])

        # Add movie
        done_status = fireEvent('status.get', 'done', single = True)
        movie = db.query(Movie).filter_by(library_id = group['library'].get('id')).first()
        if not movie:
            movie = Movie(
                library_id = group['library'].get('id'),
                profile_id = 0,
                status_id = done_status.get('id')
            )
            db.add(movie)
            db.commit()

        # Add Release
        snatched_status = fireEvent('status.get', 'snatched', single = True)
        rel = db.query(Relea).filter(
            or_(
                Relea.identifier == identifier,
                and_(Relea.identifier.startswith(group['library']['identifier']), Relea.status_id == snatched_status.get('id'))
            )
        ).first()
        if not rel:
            rel = Relea(
                identifier = identifier,
                movie = movie,
                quality_id = group['meta_data']['quality'].get('id'),
                status_id = done_status.get('id')
            )
            db.add(rel)
            db.commit()

        # Add each file type
        for type in group['files']:
            for cur_file in group['files'][type]:
                added_file = self.saveFile(cur_file, type = type, include_media_info = type is 'movie')
                try:
                    added_file = db.query(File).filter_by(id = added_file.get('id')).one()
                    rel.files.append(added_file)
                    db.commit()
                except Exception, e:
                    log.debug('Failed to attach "%s" to release: %s', (cur_file, e))

        fireEvent('movie.restatus', movie.id)

        return True

    def add2(self):
        db = get_session()

        rand = random.randrange(10000, 90000, 2)
        lib_id = getParam('lib_id')
        qua_id = getParam('qua_id')
        name = getParam('name')
        identifier = 'azerty12345678900'+ str(rand) + '00' + lib_id + '00' + qua_id

        if not lib_id or not qua_id or not name:
               return jsonified({
                      'success': False,
               })
	
        # Add movie
        done_status = fireEvent('status.get', 'done', single = True)
        snatched_status = fireEvent('status.get', 'snatched', single = True)
        movie = db.query(Movie).filter_by(library_id = lib_id).first()
        if not movie:
            log.debug('Update status to snatched')
            movie = Movie(
                library_id = lib_id,
                profile_id = 0,
                status_id = snatched_status.get('id')
            )
            db.add(movie)
            db.commit()

        # Add Release
        rls = db.query(Relea).filter_by(identifier = identifier).first()
        if not rls:
            log.debug('Add a %s release for movie %s.', (snatched_status.get('label'), movie.id))
            rls = Relea(
                identifier = identifier,
                movie = movie,
                quality_id = qua_id,
                status_id = snatched_status.get('id')
            )
            db.add(rls)
            db.commit()

        # Add ReleaseInfo
        log.debug('Add a %s releaseinfo for movie %s.', (snatched_status.get('label'), movie.id))
        infos = {'name': 'azerty', 'type': 'nzb', 'size': '700', 'description': '', 'url': '', 'age': '1', 'score': '100'}
        infos['name'] = name
        for key, value in infos.items():
            rls_info = ReleaseInfo(
                identifier = key,
                value = toUnicode(value)
            )
            rls.info.append(rls_info)
        db.commit()

        log.info('New %s release added for movie %s.', (snatched_status.get('label'), movie.id))

        return jsonified({
            'success': True,
            'identifier': identifier,
        })

    def saveFile(self, filepath, type = 'unknown', include_media_info = False):

        properties = {}

        # Get media info for files
        if include_media_info:
            properties = {}

        # Check database and update/insert if necessary
        return fireEvent('file.add', path = filepath, part = fireEvent('scanner.partnumber', file, single = True), type_tuple = Scanner.file_types.get(type), properties = properties, single = True)

    def deleteView(self):

        release_id = getParam('id')

        return jsonified({
            'success': self.delete(release_id)
        })

    def delete(self, id):

        db = get_session()

        rel = db.query(Relea).filter_by(id = id).first()
        if rel:
            rel.delete()
            db.commit()
            return True

        return False

    def clean(self, id):

        db = get_session()

        rel = db.query(Relea).filter_by(id = id).first()
        if rel:
            for release_file in rel.files:
                if not os.path.isfile(ss(release_file.path)):
                    db.delete(release_file)
            db.commit()

            if len(rel.files) == 0:
                self.delete(id)

            return True

        return False

    def ignore(self):

        db = get_session()
        id = getParam('id')

        rel = db.query(Relea).filter_by(id = id).first()
        if rel:
            ignored_status = fireEvent('status.get', 'ignored', single = True)
            available_status = fireEvent('status.get', 'available', single = True)
            rel.status_id = available_status.get('id') if rel.status_id is ignored_status.get('id') else ignored_status.get('id')
            db.commit()

        return jsonified({
            'success': True
        })

    def statusView(self):

        release_id = getParam('id')
        status = getParam('status')

        return jsonified({
            'success': self.status(release_id, status)
        })

    def status(self, release_id, status = None):

        db = get_session()
        new_status = fireEvent('status.get', status, single = True)
        ignored_status = fireEvent('status.get', 'ignored', single = True)
        deleted_status = fireEvent('status.get', 'deleted', single = True)

        rel = db.query(Relea).filter_by(id = release_id).first()
        if rel and new_status:
            log.debug('Changing status to %s for release %s', (new_status.get('label'), release_id))
            if new_status.get('id') == deleted_status.get('id'):
                self.delete(release_id)
            elif new_status.get('id') == ignored_status.get('id'):
                self.ignore(release_id)
            else:
                rel.status_id = new_status.get('id')
                db.commit()

            return True

        return False

    def download(self):

        db = get_session()
        id = getParam('id')
        status_snatched = fireEvent('status.add', 'snatched', single = True)

        rel = db.query(Relea).filter_by(id = id).first()
        if rel:
            item = {}
            for info in rel.info:
                item[info.identifier] = info.value

            # Get matching provider
            provider = fireEvent('provider.belongs_to', item['url'], provider = item.get('provider'), single = True)

            if item['type'] != 'torrent_magnet':
                item['download'] = provider.download

            success = fireEvent('searcher.download', data = item, movie = rel.movie.to_dict({
                'profile': {'types': {'quality': {}}},
                'releases': {'status': {}, 'quality': {}},
                'library': {'titles': {}, 'files':{}},
                'files': {}
            }), manual = True, single = True)

            if success:
                rel.status_id = status_snatched.get('id')
                db.commit()

            return jsonified({
                'success': success
            })
        else:
            log.error('Couldn\'t find release with id: %s', id)

        return jsonified({
            'success': False
        })
