from docxtpl import DocxTemplate
import tempfile
import logging
from typing import Dict
import os
from django.conf import settings

logger = logging.getLogger(__name__)


def generate_act_document_replacement(act):
    template_path = "klib/DocFile/Акт_замены_непериодических_изданий.docx"
    
    # Проверяем существование файла шаблона
    full_template_path = os.path.join(settings.BASE_DIR, template_path)
    logger.info(f"Trying to access template at: {full_template_path}")
    
    if not os.path.exists(full_template_path):
        logger.error(f"Template file not found at: {full_template_path}")
        raise FileNotFoundError(f"Template file not found: {template_path}")

    try:
        context = build_context_replacement(act)
        logger.info(f"Built context: {context}")
        
        document = create_docx(template_path, context)
        logger.info("Document created successfully")
        return document
    except Exception as e:
        logger.error(f"Error generating document: {str(e)}", exc_info=True)
        raise


def build_context_replacement(act):
    try:
        replace_editions_context = []
        replace_editions = act.get_replace_editions()
        logger.info(f"Found {len(replace_editions)} replace editions")
        
        for replace_edition in replace_editions:
            try:
                replaceable_number = replace_edition.replaceable_edition.inventory_number if replace_edition.replaceable_edition else "___"
                replaceable_title = replace_edition.replaceable_edition.edition.title if replace_edition.replaceable_edition and replace_edition.replaceable_edition.edition else "Название не указано"
                replacing_title = replace_edition.replacing_edition.title if replace_edition.replacing_edition else "Название не указано"
                
                replace_editions_context.append({
                    'replaceable_edition': replaceable_title,
                    'replaceable_number': replaceable_number,
                    'replacing_edition': replacing_title,
                })
            except Exception as e:
                logger.error(f"Error processing replace edition {replace_edition.id}: {str(e)}")
                continue

        replace_editions_context = ''.join([
            f"{replace_edition['replaceable_number']} {replace_edition['replaceable_edition']} заменён на {replace_edition['replacing_edition']}<w:br/>" 
            for replace_edition in replace_editions_context
        ])

        context = {
            'act_date': act.act_date.strftime("%d.%m.%Y") if act.act_date else "___",
            'act_number': str(act.act_number) if act.act_number else '___',
            'chairman_name': act.get_worker_name(act.chairman) if act.chairman else "___",
            'vice_chairman_name': act.get_worker_name(act.vice_chairman) if act.vice_chairman else "___",
            'member_1_name': act.get_worker_name(act.member_1) if act.member_1 else "___",
            'member_2_name': act.get_worker_name(act.member_2) if act.member_2 else "___",
            'member_3_name': act.get_worker_name(act.member_3) if act.member_3 else "___",
            'chairman_position': act.get_worker_position(act.chairman) if act.chairman else "___",
            'vice_chairman_position': act.get_worker_position(act.vice_chairman) if act.vice_chairman else "___",
            'member_1_position': act.get_worker_position(act.member_1) if act.member_1 else "___",
            'member_2_position': act.get_worker_position(act.member_2) if act.member_2 else "___",
            'member_3_position': act.get_worker_position(act.member_3) if act.member_3 else "___",
            'submitted_by': act.get_worker_name(act.submitted_by) if act.submitted_by else "___",
            'registered_by': act.get_worker_name(act.registered_by) if act.registered_by else "___",
            'total_excluded': act.total_excluded if act.total_excluded else 0,
            'socio_economic_count': act.socio_economic_count if act.socio_economic_count else 0,
            'technical_count': act.technical_count if act.technical_count else 0,
            'other_count': act.other_count if act.other_count else 0,
            'railway_theme_count': act.railway_theme_count if act.railway_theme_count else 0,
            'replacement': replace_editions_context,
        }
        
        logger.info("Context built successfully")
        return context
    except Exception as e:
        logger.error(f"Error building context: {str(e)}", exc_info=True)
        raise


def generate_act_document_journal(act):
    template_path = "klib/DocFile/Акт_списания_периодических_изданий.docx"
    context = build_context_journal(act)
    return create_docx(template_path, context)


def build_context_journal(act):
    context = {
        'act_date': act.act_date.strftime("%d.%m.%Y"),
        'act_number': str(act.act_number) if act.act_number else '___',
        'chairman_name': act.get_worker_name(act.chairman),
        'vice_chairman_name': act.get_worker_name(act.vice_chairman),
        'member_1_name': act.get_worker_name(act.member_1),
        'member_2_name': act.get_worker_name(act.member_2),
        'member_3_name': act.get_worker_name(act.member_3),
        'chairman_position': act.get_worker_position(act.chairman),
        'vice_chairman_position': act.get_worker_position(act.vice_chairman),
        'member_1_position': act.get_worker_position(act.member_1),
        'member_2_position': act.get_worker_position(act.member_2),
        'member_3_position': act.get_worker_position(act.member_3),
        'submitted_by': act.get_worker_name(act.submitted_by),
        'registered_by': act.get_worker_name(act.registered_by),
        'total_excluded': act.total_excluded,
        'socio_economic_count': act.socio_economic_count,
        'technical_count': act.technical_count,
        'other_count': act.other_count,
        'railway_theme_count': act.railway_theme_count,
        'selected_elements_info': check_string(act.selected_elements_info),
        'inventory_number': check_string(act.inventory_number),
    }
    return context


def generate_act_document_not_periodicals(act):
    template_path = "klib/DocFile/Акт_списания_непериодических_изданий.docx"
    context = build_context_not_periodicals(act)
    return create_docx(template_path, context)


def build_context_not_periodicals(act):
    context = {
        'act_date': act.act_date.strftime("%d.%m.%Y"),
        'act_number': str(act.act_number) if act.act_number else '___',
        'chairman_name': act.get_worker_name(act.chairman),
        'vice_chairman_name': act.get_worker_name(act.vice_chairman),
        'member_1_name': act.get_worker_name(act.member_1),
        'member_2_name': act.get_worker_name(act.member_2),
        'member_3_name': act.get_worker_name(act.member_3),
        'chairman_position': act.get_worker_position(act.chairman),
        'vice_chairman_position': act.get_worker_position(act.vice_chairman),
        'member_1_position': act.get_worker_position(act.member_1),
        'member_2_position': act.get_worker_position(act.member_2),
        'member_3_position': act.get_worker_position(act.member_3),
        'submitted_by': act.get_worker_name(act.submitted_by),
        'registered_by': act.get_worker_name(act.registered_by),
        'total_excluded': act.total_excluded,
        'socio_economic_count': act.socio_economic_count,
        'technical_count': act.technical_count,
        'other_count': act.other_count,
        'railway_theme_count': act.railway_theme_count,
        'selected_elements_info': check_string(act.selected_elements_info),
        'inventory_number': check_string(act.inventory_number),
    }
    return context


def generate_act_document_files(act):
    template_path = "klib/DocFile/Акт_списания_подшивок.docx"
    context = build_context_files(act)
    return create_docx(template_path, context)


def build_context_files(act):
    context = {
        'act_date': act.act_date.strftime("%d.%m.%Y"),
        'act_number': str(act.act_number) if act.act_number else '___',
        'chairman_name': act.get_worker_name(act.chairman),
        'vice_chairman_name': act.get_worker_name(act.vice_chairman),
        'member_1_name': act.get_worker_name(act.member_1),
        'member_2_name': act.get_worker_name(act.member_2),
        'member_3_name': act.get_worker_name(act.member_3),
        'chairman_position': act.get_worker_position(act.chairman),
        'vice_chairman_position': act.get_worker_position(act.vice_chairman),
        'member_1_position': act.get_worker_position(act.member_1),
        'member_2_position': act.get_worker_position(act.member_2),
        'member_3_position': act.get_worker_position(act.member_3),
        'submitted_by': act.get_worker_name(act.submitted_by),
        'registered_by': act.get_worker_name(act.registered_by),
        'total_excluded': act.total_excluded,
        'socio_economic_count': act.socio_economic_count,
        'technical_count': act.technical_count,
        'other_count': act.other_count,
        'railway_theme_count': act.railway_theme_count,
        'selected_elements_info': check_string(act.selected_elements_info),
        'inventory_number': check_string(act.inventory_number),
        'subscription': act.subscription,
    }
    return context


def generate_act_document_depository(act):
    template_path = "klib/DocFile/Акт_списания_дипозитарных_изданий.docx"
    context = build_context_depository(act)
    return create_docx(template_path, context)


def build_context_depository(act):
    context = {
        'act_date': act.act_date.strftime("%d.%m.%Y"),
        'act_number': str(act.act_number) if act.act_number else '___',
        'chairman_name': act.get_worker_name(act.chairman),
        'vice_chairman_name': act.get_worker_name(act.vice_chairman),
        'member_1_name': act.get_worker_name(act.member_1),
        'member_2_name': act.get_worker_name(act.member_2),
        'member_3_name': act.get_worker_name(act.member_3),
        'chairman_position': act.get_worker_position(act.chairman),
        'vice_chairman_position': act.get_worker_position(act.vice_chairman),
        'member_1_position': act.get_worker_position(act.member_1),
        'member_2_position': act.get_worker_position(act.member_2),
        'member_3_position': act.get_worker_position(act.member_3),
        'submitted_by': act.get_worker_name(act.submitted_by),
        'registered_by': act.get_worker_name(act.registered_by),
        'total_excluded': act.total_excluded,
        'socio_economic_count': act.socio_economic_count,
        'technical_count': act.technical_count,
        'other_count': act.other_count,
        'railway_theme_count': act.railway_theme_count,
        'selected_elements_info': check_string(act.selected_elements_info),
        'inventory_number': check_string(act.inventory_number),
    }
    return context


def create_docx(template: str, context: Dict[str, str]):
    try:
        doc = DocxTemplate(template)
        doc.render(context)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')

        doc.save(temp_file.name)
        return open(temp_file.name, 'rb')
    except Exception as e:
        message = 'Failed to create file docx: {}'.format(e)
        logger.exception(message)
        return message


def check_string(value: str) -> str:
    return value if value else ''


def client_short_name(client) -> str:
    return client.full_name.split()[0]
