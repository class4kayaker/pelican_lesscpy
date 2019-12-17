import os
import pelican
import hashlib
import base64
import io
import lesscpy
import lesscpy.lessc.parser
import lesscpy.lessc.formatter
from pelican.utils import sanitised_join

import logging

logger = logging.getLogger(__name__)


class Opt(object):
    def __init__(self):
        self.minify = True
        self.xminify = False
        self.tabs = False
        self.spaces = True


lesscpy_opt = Opt()

hash_funcs = {
    "sha256": hashlib.sha256,
    "sha384": hashlib.sha384,
}


class JoinError(Exception):
    pass


def compile_css_file(input_filepath, output_file):
    css_parser = lesscpy.lessc.parser.LessParser(fail_with_exc=True)

    css_fmt = lesscpy.lessc.formatter.Formatter(lesscpy_opt)
    css_parser.parse(filename=input_filepath)
    output_file.write(css_fmt.format(css_parser))


def get_css_names(generator):
    """
    Gets list of specified CSS files to be generated by lesscpy

    Configuration
    -------------
    generator.settings['LESS_INTEGRITY']:
    List

    generator.settings['LESS_CSS_FILES']:
    Dictionary with keys indicating output files
    values should be a tuple (input,output)

    Output
    ------
    generator.context['compiled_css']:
    Dictionary with keys corresponding to the configurations keys
    and values are filepaths relative to the output root
    """

    if "LESS_CSS_FILES" not in generator.settings:
        return

    hashes = generator.settings.get("LESS_INTEGRITY", [])
    versioned = generator.settings.get("VERSIONED_CSS", False)

    compiled_files = {}
    logger.info("Filling environment with lesscpy output file names")

    for key, value in generator.settings["LESS_CSS_FILES"].items():
        input_rel, output_rel = value
        hash_vals = []

        ver_string = ""

        logger.info(
            "Generating data for css file key={key}: ({input_rel})".format(
                key=key, input_rel=input_rel
            )
        )

        if hashes or versioned:
            try:
                input_path = sanitised_join(os.getcwd(), input_rel)
            except RuntimeError:
                logger.error(
                    "Skipping: file %r would be written outside output path", input_rel,
                )
                continue
            tmpio = io.StringIO()
            compile_css_file(input_path, tmpio)

        if versioned:
            ver_string = (
                "?" + hashlib.sha256(tmpio.getvalue().encode("utf-8")).hexdigest()[:6]
            )

        for h in hashes:
            if h not in hash_funcs:
                logger.error("Skipping generation of unknown hash %s", h)
                continue
            hash_vals.append(
                "{h}-{dgst}".format(
                    h=h,
                    dgst=base64.b64encode(
                        hash_funcs[h](tmpio.getvalue().encode("utf-8")).digest()
                    ).decode(),
                )
            )
        tmpio.close()

        compiled_files[key] = {
            "css_file": output_rel + ver_string,
            "integrity": " ".join(hash_vals),
        }

    generator.context["compiled_css"] = compiled_files


def compile_css_files(pelican_object):
    """
    Compiles specified less files into css files using lesscpy

    Configuration
    -------------
    generator.settings['LESS_CSS_FILES']:
    Dictionary with keys indicating output files
    values should be a tuple (input,output)
    """

    logger.info("Generating css with lesscpy")

    for key, value in pelican_object.settings["LESS_CSS_FILES"].items():
        input_rel, output_rel = value
        logger.info("Generating %s from %s using lesscpy", output_rel, input_rel)
        try:
            input_path = sanitised_join(os.getcwd(), input_rel)
        except JoinError:
            logger.error(
                "Skipping: file %r would be read outside output path", input_rel,
            )
            continue
        try:
            output_path = sanitised_join(
                pelican_object.settings["OUTPUT_PATH"], output_rel
            )
        except JoinError:
            logger.error(
                "Skipping: file %r would be written outside output path", output_rel,
            )
            continue
        out_dir = os.path.dirname(output_path)
        if not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir)
            except Exception:
                logger.error(
                    "Error creating containing directory %r", out_dir,
                )
                raise
        try:
            with open(output_path, "w") as f:
                compile_css_file(input_path, f)
        except Exception:
            logger.error(
                "Error compiling %r as less file", input_rel,
            )
            raise


def register():
    pelican.signals.generator_init.connect(get_css_names)
    pelican.signals.finalized.connect(compile_css_files)
