Getting Started
---------------

Which best describes you?

OMG I Can't Wait to Get Started and I Have Copy-Paste Functionality!
====================================================================

You can run the Simulator with the pydeploy single-liner::

  curl -L https://raw.github.com/vmalloc/pydeploy/master/scripts/bootstrapper.py | python - http://gitserver/qa/msim/blobs/raw/master/scripts/run_infinidat_simulator.pydeploy ~/.msim

Relatively Impatient
====================

::

  easy_install pydeploy
  pydeploy http://gitserver/qa/msim/blobs/raw/master/scripts/run_infinidat_simulator.pydeploy ~/.msim
  

I Have All the Time in the World!
=================================

You can take the long path::

  git clone git://gitserver/qa/msim.git
  cd msim
  python setup.py install
  run_infinidat_simulator

