"""Public catalogue numbers follow verified release dates; URLs remain identities."""
from django.db import transaction
from .comparison import alphabet


def chronology_plan(models):
    dated = sorted((m for m in models if m.published and m.released),
                   key=lambda m: (m.released, alphabet(m.name), m.slug))
    numbers = {m.pk: n for n, m in enumerate(dated, 1)}
    return {m.pk: numbers.get(m.pk) for m in models}


def renumber_chronologically(using='default', reason='release_chronology'):
    from .models import ModelVersion, PublicationRevision
    with transaction.atomic(using=using):
        models = list(ModelVersion.objects.using(using).select_for_update().all())
        numbers = chronology_plan(models)
        changed = [m for m in models if m.public_number != numbers[m.pk]]
        # NULL staging avoids transient UNIQUE conflicts when swapping numbers.
        ModelVersion.objects.using(using).filter(pk__in=[m.pk for m in changed]).update(public_number=None)
        for model in changed:
            old = model.public_number
            model.public_number = numbers[model.pk]
            ModelVersion.objects.using(using).filter(pk=model.pk).update(public_number=model.public_number)
            PublicationRevision.objects.using(using).create(
                model=model, entity_id=model.research_entity_id or model.slug,
                action='renumber_chronology', before={'public_number': old},
                after={'public_number': model.public_number, 'released': str(model.released) if model.released else None,
                       'reason': reason, 'identity': model.slug})
        return {'changed': len(changed), 'dated': sum(m.published and bool(m.released) for m in models),
                'undated': sum(m.published and not m.released for m in models)}
