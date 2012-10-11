#
#  Copyright 2008-2010 NVIDIA Corporation
#  Copyright 2009-2010 University of California
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from __future__ import with_statement     # make with visible in Python 2.5
from __future__ import absolute_import

import inspect,sys, inspect

from compiler import pyast, typeinference

class VecFunction:

    def __init__(self, fn):
        self.fn = fn
        self.__doc__ = fn.__doc__
        self.__name__ = fn.__name__
	self.xmlstr = ''

        # Type inference is deferred until the first __call__
        # invocation.  This avoids the need for procedures to be defined
        # textually before they are called.
        self.inferred_type = None
        self.inferred_shape = None

        # Parse and cache the Copperhead AST for this function
        stmts = pyast.statement_from_text(self.get_source())
        self.syntax_tree = stmts
        self.cache = {}


    def get_source(self):
        """
        Return a string containing the source code for the wrapped function.

        NOTE: This will only work if the function was defined in a file.
        We have no access to the source of functions defined at the
        interpreter prompt.
        """
        return inspect.getsource(self.fn)

    def get_globals(self):
        """
        Return the global namespace in which the function was defined.
        """
        return self.fn.func_globals

    def get_ast(self):
        """
        Return the cached Copperhead AST.
        """
        return self.syntax_tree

    def python_function(self):
        """
        Return the underlying Python function object for this procedure.
        """
        return self.fn

    def infer_type(self):
        """
        Every Copperhead function must have a valid static type.  This
        method infers the most general type for the wrapped function.
        It will raise an exception if the function is not well-typed.
        """
        typer = typeinference.TypingContext(globals=self.get_globals())

        typeinference.infer(self.syntax_tree, context=typer)
        self.inferred_type = self.syntax_tree[0].name().type

        return self.inferred_type



    def __call__(self, *args, **kwargs):
        import compiler.xmlvisitor as xmlVst 
        import pycomp
        dirname = self.fn.__name__
        #rc = pycomp.run(dirname, *args);
        rc = -1;

        #if kernel has not been compiled,
        #compile it again
        if(rc == -1):
            vst = xmlVst.xmlvisitor(args,self.get_globals())
            vst.visit(self.get_ast())
            self.xmlstr = vst.xmlstr
            # Save input and output matrices to files
            import os
            try:
                os.mkdir(dirname)
            except OSError:
                pass
            fname = dirname + '/' + dirname + '.xml'
            fout = open(fname, 'w')
            fout.write(self.xmlstr)
            fout.close()
            pycomp.setOpts(True,True,True,False,True,16);
            pycomp.func(dirname, self.xmlstr);
            pycomp.run(dirname, *args);
