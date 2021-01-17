from time import strftime
from pathlib import Path
from shutil import move
from os import chown, chmod
from pwd import getpwnam
from grp import getgrnam

def get_backup_name(plugin_name):
	
	timestamp = strftime("%d%m%Y_%H%M%S")
	
	return timestamp + "_" + plugin_name + ".tar.gz"
	
#def get_backup_name

class stat_result:
    def __init__(self, uid, gid, mode):
        self.st_uid = uid
        self.st_gid = gid
        self.st_mode = mode

    @classmethod
    def from_stat(cls, stat):
        return cls(stat.st_uid, stat.st_gid, stat.st_mode)


def n4d_mv( orig, dest, force_permissions=False, owner=None, group=None, perm=None, create_path=False):
    orig_path = Path(orig)
    dest_path = Path(dest)
    if create_path:
        dest_path.parent.mkdir( parents=create_path, exist_ok=True )
    else:
        if not dest_path.parent.exists():
            return False

    dest_perms = stat_result.from_stat(dest_path.stat()) if dest_path.exists() else stat_result(0,0,0)

    if force_permissions:
        if owner is not None : dest_perms.st_uid = getpwnam(owner).pw_uid
        if group is not None : dest_perms.st_gid = getgrnam(group).gr_gid
        if perm  is not None : dest_perms.st_mode = int( perm, 8 )
    
    move( str(orig_path), str(dest_path) )
    chown( dest_path, dest_perms.st_uid, dest_perms.st_gid )
    if force_permissions and perm is not None: 
        chmod( dest_path, dest_perms.st_mode )

    return True