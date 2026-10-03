"""Rating text uses the same configured provider as catalog/static pages."""
import json
import re
from django.core.management.base import BaseCommand,CommandError
from catalog.i18n import SUPPORTED_CODES
from catalog.translation_providers import get_provider
from catalog.rating.content import source_labels
from catalog.rating.checks import CONFIG
from catalog.rating.translations import PATH
from catalog.management.commands.rating import save_json

class Command(BaseCommand):
    help='Translate versioned Rating labels/tooltips/methodology through the existing provider'
    def add_arguments(self,parser):
        parser.add_argument('--dry-run',action='store_true')
    def handle(self,*args,**opts):
        labels=source_labels(CONFIG);provider=get_provider()
        overlay=json.loads(PATH.read_text(encoding='utf-8')) if PATH.exists() else {'text_version':'rating-methodology-v1.0','provider':provider.name,'translations':{},'sources':{}}
        for lang,values in overlay['translations'].items():
            by_source={overlay['sources'].get(key):value for key,value in values.items()}
            for key,(_ru,en) in labels.items():
                if en in by_source:values[key]=by_source[en];overlay['sources'][key]=en
        missing={lang:[(key,en) for key,(_ru,en) in labels.items() if not overlay['translations'].get(lang,{}).get(key) or overlay['sources'].get(key)!=en]
                 for lang in SUPPORTED_CODES if lang not in ('ru','en')}
        chars=sum(len(en) for rows in missing.values() for key,en in rows)
        self.stdout.write(json.dumps({'provider':provider.name,'strings':len(labels),'remaining_chars':chars,'free_tier_chars':2000000,'dry_run':opts['dry_run']}))
        if opts['dry_run']:return
        if provider.name!='azure':raise CommandError('Real configured translation provider required')
        if chars>300000:raise CommandError('Rating translation exceeds the authorized bounded batch')
        for lang,rows in missing.items():
            if not rows:continue
            encoded=[]; maps=[]
            for key,en in rows:
                params=sorted(set(re.findall(r'\{[^{}]+\}',en)))
                replacements={p:f'RATINGPARAM{i}TOKEN' for i,p in enumerate(params)}
                for p,token in replacements.items():en=en.replace(p,token)
                encoded.append(en);maps.append(replacements)
            # Keep requests below the provider's 50K character limit.
            outputs=[]
            for start in range(0,len(encoded),40):outputs.extend(provider.translate_batch(encoded[start:start+40],lang))
            for (key,en),translated,replacements in zip(rows,outputs,maps):
                for p,token in replacements.items():
                    if token not in translated:raise CommandError('Translation lost placeholder: '+lang+' '+key)
                    translated=translated.replace(token,p)
                if not translated:raise CommandError('Empty translation: '+lang+' '+key)
                overlay['translations'].setdefault(lang,{})[key]=translated
            save_json(PATH,overlay)
            self.stdout.write(lang+': '+str(len(rows))+' strings translated')
        overlay['sources']={key:en for key,(_ru,en) in labels.items()}
        save_json(PATH,overlay)
