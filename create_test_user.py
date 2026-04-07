from db import ensure_schema, add_user

if __name__ == '__main__':
    try:
        ensure_schema()
        ok1 = add_user('admin', 'admin', 'admin')
        ok2 = add_user('user', 'user', 'user')
        print('admin created:', ok1)
        print('user created:', ok2)
    except Exception as e:
        print('Error:', e)

