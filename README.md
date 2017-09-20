# divine-pak

A quickly-written utility to parse the Divinity: Original Sin 2 PAK file
format. Currently only supports reading.

# Installation

    pip install git+git://github.com/tktech/divine-pak.git

# CLI

This module includes a command line utility.

    divine-pak --help           
    Usage: divine-pak [OPTIONS] COMMAND [ARGS]...                  
							       
    Options:                                                       
      --help  Show this message and exit.                          
							       
    Commands:                                                      
      details  Print detailed information for the given...         
      extract  Extract the given path/name from the archive,...    
      list     Print a list of all files contained within...       
