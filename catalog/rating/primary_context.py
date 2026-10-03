"""Deterministic model-only context routing, independent of evidence availability."""
import re

def primary_context(row):
    text = ' '.join(str(row.get(k) or '') for k in ('Name','Tasks','Output Modalities')).lower()
    output = str(row.get('Output Modalities') or '').lower()
    inputs = str(row.get('Input Modalities') or '').lower()
    tasks = str(row.get('Tasks') or '').lower()
    if re.search(r'embed|retrieval|rerank', text): return 'EMB.RETRIEVAL'
    if re.search(r'safety|moderation|classifier|jailbreak', tasks): return 'SAFETY.CLASSIFIER'
    if re.search(r'\bocr\b', str(row.get('Name') or '').lower()): return 'DOC.OCR'
    if re.search(r'protein|molecule|biolog|alphafold|esmfold|boltz|drug', text): return 'SCI.STRUCTURE'
    if re.search(r'robot|physical.action', tasks): return 'ROBOT.ACTION'
    if re.search(r'forecast|time.series', tasks): return 'SCI.FORECAST'
    if re.search(r'3d',tasks): return '3D.GEN'
    if re.search(r'motion',tasks): return 'MOTION.GEN'
    if re.search(r'music|sound_effect|audio_generation', tasks): return 'AUD.MUSIC'
    if re.search(r'voice.agents?|realtime.voice', tasks): return 'VOICE.AGENT'
    if 'audio' in output and 'text' not in output and not any(x in output for x in ('video','image')):
        return 'TTS.REALTIME' if 'stream' in tasks or 'realtime' in tasks else 'TTS.NARRATION'
    if 'audio' in inputs and output.strip()=='text' and str(row.get('Category'))=='audio':
        return 'STT.STREAMING' if 'stream' in tasks else 'STT.TRANSCRIBE'
    if ('video' in output and 'text' not in output) or re.search(r'video_(generation|editing)|character_animation',tasks): return 'VID.GEN'
    if ('image' in output and 'text' not in output) or re.search(r'image_(generation|editing)|text_to_image',tasks):
        return 'IMG.EDIT' if re.search(r'image_edit|image-to-image|editing',tasks) else 'IMG.GEN'
    if 'text' in output or str(row.get('Category'))=='text' or re.search(r'\btext\b|reasoning|coding|agents|vision|document|multilingual',tasks):
        return 'LLM.OVERALL'
    if str(row.get('Category'))=='audio':
        if re.search(r'asr|scribe|transcri|whisper',text): return 'STT.TRANSCRIBE'
        if re.search(r'tts|speech_generation|speech_editing|dubbing',text): return 'TTS.NARRATION'
        return 'VOICE.AGENT'
    raise ValueError('No primary_rating_context: '+str(row.get('Record ID')))

EXTRA_CONTEXTS = {
    'SCI.STRUCTURE': {'context_id':'SCI.STRUCTURE','status':'Insufficient Data','reason':'Scientific structure models; contextual estimates only'},
    'SCI.FORECAST': {'context_id':'SCI.FORECAST','status':'Insufficient Data','reason':'Time-series models; contextual estimates only'},
    'ROBOT.ACTION': {'context_id':'ROBOT.ACTION','status':'Insufficient Data','reason':'Physical action models; contextual estimates only'},
    '3D.GEN': {'context_id':'3D.GEN','status':'Insufficient Data','reason':'3D generation; contextual estimates only'},
    'MOTION.GEN': {'context_id':'MOTION.GEN','status':'Insufficient Data','reason':'Motion generation; contextual estimates only'},
}
