<?php
declare(strict_types=1);
namespace Ted2;

/** Additive migration: never resets existing accounts, approved content or themes. */
final class Upgrade62
{
    public static function apply(Store $store): array
    {
        $db = $store->db;
        $db->query('CREATE TABLE IF NOT EXISTS pulse_seen(identity TEXT PRIMARY KEY, record_id TEXT NOT NULL, seen_at TEXT NOT NULL)');
        if ($db->one("SELECT value FROM v6_meta WHERE key='migration-6.2'")) return ['already_upgraded' => true];
        $backup = dirname($db->path).'/pre-v6.2-'.gmdate('Ymd-His').'-'.id().'.sqlite3';
        $db->query('VACUUM INTO ?', [$backup]); @chmod($backup, 0600);
        $count = 0;
        $db->tx(function () use ($db, $store, &$count): void {
            foreach (Schema::all() as $collection => $schema) {
                foreach ($store->list($collection) as $record) {
                    $changed = false; $version = $record['_version'];
                    unset($record['_version'], $record['_updated_at']);
                    foreach ($schema['fields'] as $field) {
                        if (!array_key_exists($field['key'], $record)) {
                            $record[$field['key']] = Schema::default($field); $count++; $changed = true;
                        }
                    }
                    if($collection==='theme'){foreach(['pulse','quotes'] as $block)if(!in_array($block,$record['home_blocks']??[],true)){$at=array_search('facts',$record['home_blocks'],true);array_splice($record['home_blocks'],$at===false?2:$at+1,0,[$block]);$changed=true;}}
                    if ($changed) $store->replace($collection, $record, $version, 'migration-v6.2');
                }
            }
            $seed = decode(file_get_contents(ROOT.'/data/seed.json'));
            foreach ($seed['science_quotes'] ?? [] as $record) {
                if (!$store->get('science_quotes', $record['id'], true) && !$db->one('SELECT id FROM trash WHERE collection=? AND id=?', ['science_quotes', $record['id']])) {
                    $store->insert('science_quotes', $record, 'migration-v6.2');
                }
            }
            $db->query("INSERT INTO v6_meta VALUES('migration-6.2',?)", [utc()]);
            $store->audit('server-operator', 'migrate-v6.2', 'settings', 'laboratory');
        });
        return ['backup'=>$backup, 'added_defaults'=>$count, 'quotations'=>'Six private records are ready for attribution review. Automatic public headlines are off until enabled.'];
    }

    public static function validate(string $collection, array $p): void
    {
        if ($collection === 'theme') {
            foreach (['quote_seconds'=>[5,120], 'pulse_max'=>[1,20], 'public_cache_entries'=>[10,100], 'render_cache_seconds'=>[0,600]] as $key=>$bounds) {
                ensure(is_numeric($p[$key]) && $p[$key]>=$bounds[0] && $p[$key]<=$bounds[1],422, $key.' is out of range.');
            }
        }
        if ($collection === 'settings') {
            foreach (['pulse_lookback'=>[1,180], 'pulse_refresh_hours'=>[1,168]] as $key=>$bounds) {
                ensure(is_numeric($p[$key]) && $p[$key]>=$bounds[0] && $p[$key]<=$bounds[1],422,$key.' is out of range.');
            }
            ensure(count($p['pulse_topics'])<=12,422,'Use at most twelve public topic filters.');
            foreach ($p['pulse_topics'] as $topic) ensure(strlen($topic)<=90,422,'Keep each topic under 90 characters.');
        }
        if ($collection === 'science_quotes' && $p['visibility']==='public') {
            ensure($p['approved']===true,422,'Review quotation wording, attribution and rights before approving.');
            ensure($p['license']!=='',422,'Add the quotation rights statement.');
            if ($p['attribution_type']!=='original') ensure($p['source_url']!=='',422,'Attributed quotations need a verifiable source.');
        }
        if ($collection === 'science_news' && $p['visibility']==='public') {
            ensure($p['approved'] || $p['automatic'],422,'Approve this headline or select automatic source-headline mode.');
        }
        if (isset($p['tags'])) {
            ensure(count($p['tags'])<=12,422,'Use at most twelve hashtags.');
            foreach ($p['tags'] as $tag) ensure(preg_match('/^#?[\pL\pN][\pL\pN _-]{0,49}$/uD',$tag)===1,422,'Hashtags may contain letters, numbers, spaces, underscores and hyphens.');
        }
    }
}
