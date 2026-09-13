<?php
declare(strict_types=1);
namespace Ted2;
const ROOT = __DIR__ . '/..';
const VERSION = '6.0.0';
foreach (['Core','Database','Records','Auth','Media','PublicSite','Publisher','Literature','Application'] as $name) require_once __DIR__ . '/' . $name . '.php';
Config::load();
