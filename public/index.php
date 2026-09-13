<?php
declare(strict_types=1);
require __DIR__.'/../php/bootstrap.php';
try {(new \Ted2\Application())->run();}
catch (\Ted2\Problem $e){http_response_code($e->status);header('Cache-Control: no-store');header('Content-Type: application/json; charset=utf-8');echo \Ted2\json(['error'=>$e->getMessage()]);}
catch (\Throwable $e){error_log('TED2 request failed: '.get_class($e).' '.$e->getMessage());http_response_code(500);header('Cache-Control: no-store');header('Content-Type: application/json; charset=utf-8');echo \Ted2\json(['error'=>'The request could not be completed. Check the private server log; no success was assumed.']);}
