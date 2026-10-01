<?php
declare(strict_types=1);
namespace Ted2;

/** Private authoring, portable ZIP export and an explicit Overleaf hand-off. No TeX executes here. */
final class Writing7
{
    public static function record(Store $s,array $u,string $id):array
    {
        $p=$s->get('writing_projects',$id);
        ensure($p!==null,404,'Writing project not found.');
        ensure((new Records($s))->canRead($u,'writing_projects',$p),403,'This writing project belongs to another researcher.');
        return $p;
    }
    public static function template(string $kind):string
    {
        $sections=match($kind){
            'review'=>['Abstract','Introduction','Scope and search strategy','Evidence synthesis','Limitations','Conclusions'],
            'protocol'=>['Purpose and scope','Approvals and safety','Materials','Methodology','Quality controls','Analysis plan','Records and deviations'],
            'report'=>['Abstract','Introduction','Materials and methods','Results','Discussion','Conclusions'],
            default=>throw new Problem(422,'Choose Report, Review or Protocol.')
        };
        $body="% Private working document. Replace the title and author in the editor.\n% No data, approvals, results or methods are inferred by this template.\n\\documentclass[12pt,a4paper]{article}\n\\usepackage[T1]{fontenc}\n\\usepackage[utf8]{inputenc}\n\\usepackage[margin=25mm]{geometry}\n\\usepackage{graphicx,booktabs,amsmath}\n\\usepackage[hidelinks]{hyperref}\n\\title{Research working document}\n\\author{}\n\\date{\\today}\n\\begin{document}\n\\maketitle\n";
        foreach($sections as $section)$body.="\n\\section{".$section."}\n% Draft your own verified content here.\n";
        return $body."\n% Uncomment after adding citations and entries to references.bib:\n% \\bibliographystyle{plain}\n% \\bibliography{references}\n\\end{document}\n";
    }
    /** Small uncompressed ZIP writer; independent of the optional PHP ZIP extension. */
    public static function zip(array $files):string
    {
        $out='';$directory='';$count=0;
        foreach($files as $name=>$bytes){
            ensure(preg_match('/^[a-z0-9_.-]+$/iD',$name)===1,422,'Unsafe export filename.');
            $offset=strlen($out);$length=strlen($bytes);$crc=crc32($bytes);
            $out.=pack('VvvvvvVVVvv',0x04034b50,20,0,0,0,33,$crc,$length,$length,strlen($name),0).$name.$bytes;
            $directory.=pack('VvvvvvvVVVvvvvvVV',0x02014b50,20,20,0,0,0,33,$crc,$length,$length,strlen($name),0,0,0,0,0,$offset).$name;$count++;
        }
        $offset=strlen($out);$out.=$directory;
        return $out.pack('VvvvvVVv',0x06054b50,0,0,$count,$count,strlen($directory),$offset,0);
    }
    public static function export(array $p):string
    {
        ensure(trim($p['main_tex']??'')!=='',422,'Save some LaTeX source before exporting.');
        return self::zip(['main.tex'=>$p['main_tex'],'references.bib'=>$p['bibtex']??'','README.txt'=>"TED2 private writing export\n\nOpen main.tex in your preferred LaTeX editor.\nThe tracker does not execute TeX commands. Overleaf compiles this source after you explicitly transfer it and sign in as required.\nThis creates a new copy, not automatic bidirectional synchronization.\nOnly the saved LaTeX and bibliography are exported; attached private lab records are not included.\n"]);
    }
}
