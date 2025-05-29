// Test lab 1 .so files for formal conformance
//
// Compile with:
// gcc -o lab1test lab1test.c -ldl
//
// (c) Alexei Guirik, 2021
// This source is licensed under CC BY-NC 4.0 
// (https://creativecommons.org/licenses/by-nc/4.0/)
//  

#include <stdio.h>
#include <string.h>
#include <dlfcn.h>

#include "plugin_api.h"


int main(int argc, char *argv[]) {
    if (argc == 1) {
        fprintf(stdout, "Usage: lab1test /path/to/lib1.so ... libN.so\n");
        return 0;
    }

    // Try all names that are passed via argv
    for (int i = 1; i < argc; i++) {
        fprintf(stdout, "Trying %s:\n", argv[i]);
        
        struct plugin_info pi = {0};
        
        void *dl = dlopen(argv[i], RTLD_LAZY);
        if (!dl) {
            fprintf(stderr, "ERROR: dlopen() failed: %s\n", dlerror());
            continue;
        }

        // Check for plugin_get_info() func
        void *func = dlsym(dl, "plugin_get_info");
        if (!func) {
            fprintf(stderr, "ERROR: dlsym() failed: %s\n", dlerror());
            goto END;
        }
        
        typedef int (*pgi_func_t)(struct plugin_info*);
        pgi_func_t pgi_func = (pgi_func_t)func;            
    
        int ret = pgi_func(&pi);
        if (ret < 0) {        
            fprintf(stderr, "ERROR: plugin_get_info() failed\n");
            goto END;
        }
 
        // Plugin info       
        fprintf(stdout, "Plugin purpose:\t\t%s\n", pi.plugin_purpose);
        fprintf(stdout, "Plugin author:\t\t%s\n", pi.plugin_author);
        fprintf(stdout, "Supported options: ");
        if (pi.sup_opts_len > 0) {
            fprintf(stdout, "\n");
            for (size_t i = 0; i < pi.sup_opts_len; i++) {
                fprintf(stdout, "\t--%s\t\t%s\n", pi.sup_opts[i].opt.name, pi.sup_opts[i].opt_descr);
            }
        }
        else {
            fprintf(stdout, "none (!?)\n");
        }

        // Warn if plugin_process_file() is not found
        func = dlsym(dl, "plugin_process_file");
        if (!func) {
            fprintf(stderr, "WARNING: no plugin_process_file() function found\n");
        }
        
        END:
        if (dl) dlclose(dl);
    }
    return 0;
}
