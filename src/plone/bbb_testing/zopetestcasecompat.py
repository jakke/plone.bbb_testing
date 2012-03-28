import unittest
import sys
import re
import  base64
import transaction

import AccessControl.Permissions

import plone.testing.z2

folder_name = 'test_folder_1_'
user_name = 'test_user_1_'
user_password = 'secret'
user_role = 'test_role_1_'
standard_permissions = [AccessControl.Permissions.access_contents_information,
    AccessControl.Permissions.view]


def savestate(func):
    '''Decorator saving thread local state before executing func
       and restoring it afterwards.
    '''
    from AccessControl.SecurityManagement import getSecurityManager
    from AccessControl.SecurityManagement import setSecurityManager
    from zope.site.hooks import getSite
    from zope.site.hooks import setSite

    def wrapped_func(*args, **kw):
        sm, site = getSecurityManager(), getSite()
        try:
            return func(*args, **kw)
        finally:
            setSecurityManager(sm)
            setSite(site)
    return wrapped_func


class ZTCCompatTestCase(unittest.TestCase):

    def setUp(self):
        self.app = self.layer['app']
        self.setUpCompat()
        self.afterSetUp()

    def afterSetUp(self):
        pass

    def setRoles(self, roles):
        plone.testing.z2.setRoles(self.folder.acl_users, user_name, roles)

    def tearDown(self):
        self.beforeTearDown()
        self.tearDownCompat()

    def beforeTearDown(self):
        pass

    def setUpCompat(self):
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        plone.testing.z2.login(self.folder.acl_users, user_name)

    def _setupFolder(self):
        '''Creates and configures the folder.'''
        app = self.app
        from OFS.Folder import manage_addFolder
        manage_addFolder(app, folder_name)
        folder = getattr(app, folder_name)
        folder._addRole(user_role)
        folder.manage_role(user_role, standard_permissions)
        self.folder = folder

    def _setupUserFolder(self):
        '''Creates the user folder.'''
        from AccessControl.User import manage_addUserFolder
        manage_addUserFolder(self.folder)

    def _setupUser(self):
        '''Creates the default user.'''
        uf = self.folder.acl_users
        uf.userFolderAddUser(user_name, user_password, [user_role], [])

    def tearDownCompat(self):
        del self.folder

    @savestate
    def publish(self, path, basic=None, env=None, extra=None,
                request_method='GET', stdin=None, handle_errors=True):
        '''Publishes the object at 'path' returning a response object.'''

        from StringIO import StringIO
        from ZPublisher.Request import Request
        from ZPublisher.Response import Response
        from ZPublisher.Publish import publish_module

        # Commit the sandbox for good measure
        transaction.commit()

        if env is None:
            env = {}
        if extra is None:
            extra = {}

        request = self.app.REQUEST

        env['SERVER_NAME'] = request['SERVER_NAME']
        env['SERVER_PORT'] = request['SERVER_PORT']
        env['REQUEST_METHOD'] = request_method

        p = path.split('?')
        if len(p) == 1:
            env['PATH_INFO'] = p[0]
        elif len(p) == 2:
            [env['PATH_INFO'], env['QUERY_STRING']] = p
        else:
            raise TypeError, ''

        if basic:
            env['HTTP_AUTHORIZATION'] = "Basic %s" % base64.encodestring(basic)

        if stdin is None:
            stdin = StringIO()

        outstream = StringIO()
        response = Response(stdout=outstream, stderr=sys.stderr)
        request = Request(stdin, env, response)
        for k, v in extra.items():
            request[k] = v

        publish_module('Zope2',
                       debug=not handle_errors,
                       request=request,
                       response=response,
                      )

        return ResponseWrapper(response, outstream, path)


class ResponseWrapper:
    '''Decorates a response object with additional introspective methods.'''

    _bodyre = re.compile('\r\n\r\n(.*)', re.MULTILINE | re.DOTALL)

    def __init__(self, response, outstream, path):
        self._response = response
        self._outstream = outstream
        self._path = path

    def __getattr__(self, name):
        return getattr(self._response, name)

    def getOutput(self):
        '''Returns the complete output, headers and all.'''
        return self._outstream.getvalue()

    def getBody(self):
        '''Returns the page body, i.e. the output par headers.'''
        body = self._bodyre.search(self.getOutput())
        if body is not None:
            body = body.group(1)
        return body

    def getPath(self):
        '''Returns the path used by the request.'''
        return self._path

    def getHeader(self, name):
        '''Returns the value of a response header.'''
        return self.headers.get(name.lower())

    def getCookie(self, name):
        '''Returns a response cookie.'''
        return self.cookies.get(name)
