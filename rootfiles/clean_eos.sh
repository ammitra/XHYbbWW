#!/bin/bash
for i in `xrdfsls  /store/user/ammitra/XHYbbWW/selection | grep WJets_`; do eosrm $i; done;
for i in `xrdfsls  /store/user/ammitra/XHYbbWW/selection | grep ZJets_`; do eosrm $i; done;
for i in `xrdfsls  /store/user/ammitra/XHYbbWW/selection | grep ttbar_`; do eosrm $i; done;
