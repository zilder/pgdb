import psycopg2
import argparse

class Debugger:
    def __init__(self, db, user):
        self.func_oid = -1
        self.line_no = -1
        self.func_name = '(None)'
        self.last_cmd = ''
        self.connection = self._connect(db, user, '')
        # self.session_id = -1

    def _connect(self, dbname, username, password):
        print 'Connecting to database...',
        try:
            self.con = psycopg2.connect(database=dbname, user=username, password=password)
            self.cur = self.con.cursor()
            print 'done'
        except Exception, e:
            print 'failed'
            raise e
        self.cur.execute('SELECT * FROM pldbg_create_listener();')
        self.session_id = self.cur.fetchone()[0]
        print 'session id:', self.session_id
        # self.cur.execute('SELECT pldbg_set_global_breakpoint(%s, \'test\'::regproc::oid, NULL, NULL);',
        #                 (self.session_id, ))

    def close(self):
        self.cur.close()
        self.con.close()

    def _get_func_line(self, func_oid, line_no):
        self.cur.execute('SELECT * FROM pldbg_get_source(%s, %s);',
                         (self.session_id, self.func_oid))
        func_body = self.cur.fetchone()[0]
        return func_body.split('\n')[line_no-2]

    def _print_current_breakpoint(self):
        self.func_oid, self.line_no, self.func_name = self.cur.fetchone()
        print self.line_no, ':', self._get_func_line(self.func_oid, self.line_no)

    def run(self):
        self.cur.execute('SELECT * FROM pldbg_wait_for_target(%s);', (self.session_id, ))
        self.cur.execute('SELECT * FROM pldbg_wait_for_breakpoint(%s);', (self.session_id, ))
        self._print_current_breakpoint()

    def next(self):
        ''' Do next '''
        self.cur.execute('SELECT * FROM pldbg_step_over(%s);', (self.session_id, ))
        self._print_current_breakpoint()

    def step_into(self):
        ''' Step into '''
        self.cur.execute('SELECT * FROM pldbg_step_into(%s);', (self.session_id, ))
        self._print_current_breakpoint()

    def continue_execution(self):
        ''' Continue execution until the next breakpoint or end of function '''
        self.cur.execute('SELECT * FROM pldbg_continue(%s);', (self.session_id, ))
        self._print_current_breakpoint()

    def print_variable(self, var_name):
        ''' Print variable value '''
        self.cur.execute('SELECT name, value FROM pldbg_get_variables(%s) WHERE name=%s;',
                         (self.session_id, var_name))
        for rec in self.cur.fetchall():
            print rec[0], '=', rec[1]

    def set_breakpoint(self, arg):
        # TODO: check if breakpoint is already exists
        self.cur.execute('SELECT pldbg_set_global_breakpoint(%s, %s::regproc::oid, NULL, NULL);',
                         (self.session_id, arg))

    def print_listing(self):
        ''' Prints function body '''
        self.cur.execute('SELECT * FROM pldbg_get_source(%s, %s);', (self.session_id, self.func_oid))
        func_body = self.cur.fetchone()[0]
        for ln, line_text in enumerate(func_body.split('\n'), 1):
          print ln, '\t', line_text

    def handle_command(self, cmd, arg):
        cmd = cmd.lower()
        if cmd in ('r', 'run'):
            self.run()
        if cmd in ('n', 'next'):
            self.next()
        elif cmd in ('s', 'step'):
            self.step_into()
        elif cmd in ('c', 'continue'):
            self.continue_execution()
        elif cmd in ('p', 'print'):
            self.print_variable(arg)
        elif cmd in ('b', 'breakpoint'):
            self.set_breakpoint(arg)
        elif cmd in ('i', 'info'):
            if arg in ('b', 'breakpoint'):
                self.cur.execute('SELECT func::regproc, linenumber FROM pldbg_get_breakpoints(1);')
                for rec in self.cur:
                    print rec[0], ':', rec[1]
        elif cmd in ('l', 'list'):
            self.print_listing()

def main(db, user, func):
    print 'pgdb started'

    dbg = Debugger(db, user)
    if func:
        dbg.set_breakpoint(func)
        dbg.run()

    while True:
        raw_cmd = raw_input("> ").strip()
        # if user doesn't enter anything the just repeat last command
        if not raw_cmd:
            raw_cmd = last_cmd
        else:
            last_cmd = raw_cmd

        # get argument
        pos = raw_cmd.find(' ')
        if pos > 0:
            cmd = raw_cmd[0:pos]
            arg = raw_cmd[pos:].strip()
        else:
            cmd = raw_cmd
            arg = None
        dbg.handle_command(cmd, arg)

    dbgr.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pgdb - postgres plpgsql debugger')
    # parser.add_argument('--host', type=string, default='localhost', help='postgres server host')
    # parser.add_argument('--port', type=int, default=5432, help='postgres server port')
    parser.add_argument('--user', dest='user', default='postgres', help='user name')
    parser.add_argument('--database', dest='db', default='postgres', help='database name')
    parser.add_argument('--func', dest='func', help='plpgsql function to debug')
    args = parser.parse_args()
    main(args.db, args.user, args.func)
