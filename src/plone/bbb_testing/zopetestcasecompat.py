import unittest

import AccessControl.Permissions

import plone.testing.z2

folder_name = 'test_folder_1_'
user_name = 'test_user_1_'
user_password = 'secret'
user_role = 'test_role_1_'
standard_permissions = [AccessControl.Permissions.access_contents_information,
    AccessControl.Permissions.view]


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
