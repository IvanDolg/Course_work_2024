from docxtpl import DocxTemplate
import tempfile
import logging

logger = logging.getLogger(__name__)

def generate_password_document(user, password):
    template_path = "kuser/DocFile/Иное_физическое_лицо_креды.docx"
    context = build_password_context(user, password)
    return create_docx(template_path, context)

def build_password_context(user, password):
    context = {
        'username': user.username,
        'password': password,
    }
    return context

def create_docx(template: str, context: dict):
    try:
        doc = DocxTemplate(template)
        doc.render(context)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')

        doc.save(temp_file.name)
        return open(temp_file.name, 'rb')
    except Exception as e:
        logger.exception(f'Failed to create docx file: {e}')
        return None