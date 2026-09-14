<?php
declare(strict_types=1);
namespace Ted2;
const ROOT = __DIR__ . '/..';
const VERSION = '6.2.0';
foreach (['Core','Database','Records','Auth','Media','PublicSite','Publisher','Literature','Application','Upgrade61','Design','Tracking','Studio61','Public61','Upgrade62','Experience62','Pulse','Cache62','Studio62'] as $name) require_once __DIR__ . '/' . $name . '.php';
Config::load();
