#!/usr/bin/env python3
"""Resolve the Odoo runtime of the current project, trace models/fields/methods/xmlids/routes, and scan a
module for APIs that break when porting it to another version (up or down).

Author: aghyksa (https://aghyksa.com). Read-only, stdlib only.

Usage:
  odoo_env.py [--conf PATH] env
  odoo_env.py [--conf PATH] model MODEL
  odoo_env.py [--conf PATH] field MODEL FIELD
  odoo_env.py [--conf PATH] method MODEL METHOD
  odoo_env.py [--conf PATH] xmlid MODULE.NAME
  odoo_env.py [--conf PATH] routes MODULE
  odoo_env.py port-scan MODULE_PATH --to VERSION [--from VERSION]
  odoo_env.py selftest
"""
import argparse
import ast
import configparser
import glob
import json
import os
import re
import sys
import tempfile

CONF_DIRS = [os.path.expanduser(p) for p in
             os.environ.get("ODOO_CONF_DIRS", os.pathsep.join(["~/odoo/conf", "/etc/odoo"])).split(os.pathsep) if p]
RC_FILES = [os.path.expanduser(p) for p in ("~/.odoorc", "~/.openerp_serverrc")]
LAUNCH_FILES = (os.path.join(".vscode", "launch.json"), os.path.join(".claude", "launch.json"))
SKIP_DIRS = ("tests", "__pycache__", "static", "migrations")


def die(msg):
    print("SETUP ERROR: %s" % msg)
    sys.exit(2)


def read(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def parents(cwd):
    path = cwd
    while True:
        yield path
        if path == os.path.dirname(path):
            return
        path = os.path.dirname(path)


def opt_value(args, names):
    for idx, arg in enumerate(args):
        if arg in names and idx + 1 < len(args):
            return args[idx + 1]
        for name in names:
            if name.startswith("--") and arg.startswith(name + "="):
                return arg.split("=", 1)[1]
    return None


def load_jsonc(path):
    # launch.json allows // comment lines and trailing commas
    text = "\n".join(l for l in read(path).splitlines() if not l.lstrip().startswith("//"))
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def confs_from_launch(cwd):
    # every odoo-bin -c <conf> config of the nearest .vscode/ or .claude/ launch.json (cwd or a parent)
    for path in parents(cwd):
        found = []
        for rel in LAUNCH_FILES:
            launch = os.path.join(path, rel)
            if not os.path.isfile(launch):
                continue
            try:
                configs = load_jsonc(launch).get("configurations", [])
            except (ValueError, AttributeError):
                configs = []
            for cfg in configs:
                args = [str(a).replace("${workspaceFolder}", path) for a in
                        [cfg.get("program", ""), cfg.get("module", "")] + list(cfg.get("runtimeArgs", [])) +
                        list(cfg.get("args", []))]
                conf = opt_value(args, ("-c", "--config"))
                if conf and any(a.endswith(("odoo-bin", "odoo")) for a in args):
                    found.append((os.path.join(path, os.path.expanduser(conf)), opt_value(args, ("-d", "--database")),
                                  "%s [%s]" % (launch, cfg.get("name", "?"))))
        if found:
            return found
    return []


def addons_path(conf):
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read(conf, encoding="utf-8")
    except (configparser.Error, UnicodeDecodeError):
        return [], None
    raw = parser.get("options", "addons_path", fallback="")
    db = parser.get("options", "db_name", fallback="") or None
    return [os.path.expanduser(p.strip()) for p in raw.split(",") if p.strip()], db


def conf_from_cwd(cwd):
    # conf (project tree, ~/.odoorc, ODOO_CONF_DIRS) whose addons_path covers cwd most deeply
    best, best_len = None, -1
    confs = [c for d in list(parents(cwd)) + CONF_DIRS for c in glob.glob(os.path.join(d, "*.conf"))] + RC_FILES
    for conf in [c for c in confs if os.path.isfile(c)]:
        roots, _db = addons_path(conf)
        for root in roots:
            root = os.path.realpath(root)
            if (cwd == root or cwd.startswith(root + os.sep) or root.startswith(cwd + os.sep)) and len(root) > best_len:
                best, best_len = conf, len(root)
    return best


def odoo_root_of(roots):
    # dir holding odoo/release.py: a source checkout (next to odoo-bin) or site-packages (deb/pip install)
    for root in roots:
        real = os.path.realpath(root)
        for cand in (os.path.dirname(real), os.path.dirname(os.path.dirname(real))):
            if os.path.isfile(os.path.join(cand, "odoo", "release.py")):
                return cand
    return None


def python_of(odoo_root):
    homes = [os.path.join(odoo_root, d) for d in (".venv", "venv")] + [os.environ.get("VIRTUAL_ENV", "")]
    exes = [os.path.join(h, *exe) for h in homes if h for exe in (("bin", "python3"), ("Scripts", "python.exe"))]
    return next((p for p in exes if os.path.isfile(p)), "- (no venv next to odoo-bin and no $VIRTUAL_ENV)")


def version_of(odoo_root):
    match = re.search(r"version_info\s*=\s*\((\d+),\s*(\d+)", read(os.path.join(odoo_root, "odoo", "release.py")))
    return "%s.%s" % match.groups() if match else "?"


def manifest_major(path):
    match = re.search(r"""['"]version['"]\s*:\s*['"](\d{2})\.0\.""", read(path))
    return match and match.group(1)


def manifest_majors(roots, odoo_root):
    counts = {}
    for root in roots:
        if os.path.realpath(root).startswith(odoo_root + os.sep):
            continue
        for manifest in glob.glob(os.path.join(root, "*", "__manifest__.py")):
            major = manifest_major(manifest)
            if major:
                counts[major] = counts.get(major, 0) + 1
    return counts


def describe(conf, db, source):
    if not conf or not os.path.isfile(conf):
        return None
    roots, conf_db = addons_path(conf)
    odoo_root = odoo_root_of(roots)
    if not odoo_root:
        return None
    ordered = []
    for root in [os.path.join(odoo_root, "odoo", "addons")] + [r for r in roots if os.path.isdir(r)]:
        real = os.path.realpath(root)
        if real not in ordered:
            ordered.append(real)
    return {
        "version": version_of(odoo_root), "odoo_root": odoo_root, "conf": conf, "conf_source": source,
        "db": db or conf_db or os.path.splitext(os.path.basename(conf))[0],
        "python": python_of(odoo_root), "roots": ordered, "notes": [],
    }


def resolve(conf=None, cwd=None):
    cwd = os.path.realpath(cwd or os.getcwd())
    if conf:
        cands = [(conf, None, "--conf")]
    elif os.environ.get("ODOO_RC"):
        cands = [(os.environ["ODOO_RC"], None, "$ODOO_RC")]
    else:
        cands = confs_from_launch(cwd) or [(conf_from_cwd(cwd), None, "addons_path covers cwd")]
    envs = [e for e in (describe(*c) for c in cands) if e]
    if not envs:
        die("no Odoo conf found for %s (checked $ODOO_RC, launch.json, *.conf in the project tree, ~/.odoorc, "
            "ODOO_CONF_DIRS); pass --conf <path/to/odoo.conf>. The conf's addons_path must reach the Odoo "
            "source (odoo/release.py) on this disk" % cwd)
    counts = manifest_majors(envs[0]["roots"], envs[0]["odoo_root"])
    major = max(counts, key=counts.get) if counts else None
    env = next((e for e in envs if major and e["version"].split(".")[0] == major), envs[0])
    if len(envs) > 1:
        env["notes"].append("launch configs: " + ", ".join("%s=%s" % (e["conf_source"].split("[")[-1].rstrip("]"),
                                                                       e["version"]) for e in envs))
    if major and env["version"].split(".")[0] != major:
        env["notes"].append("WARNING: project manifests are mostly %s.0 %s but this conf runs %s; pass --conf"
                            % (major, counts, env["version"]))
    elif env is not envs[0]:
        env["notes"].append("picked the launch config matching the project manifests (%s.0 %s)" % (major, counts))
    return env


def modules(env):
    # first module per name wins, same as Odoo's addons_path order
    found = {}
    for root in env["roots"]:
        for manifest in glob.glob(os.path.join(root, "*", "__manifest__.py")):
            found.setdefault(os.path.basename(os.path.dirname(manifest)), os.path.dirname(manifest))
    return found


def py_files(path, skip=SKIP_DIRS):
    for base, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(base, name)


def class_blocks(text, model):
    # (kind, start offset, block text) for each top-level class that defines or extends `model`
    quoted = r"""['"]%s['"]""" % re.escape(model)
    starts = [m.start() for m in re.finditer(r"^class \w", text, re.M)] + [len(text)]
    for begin, end in zip(starts, starts[1:]):
        block = text[begin:end]
        name = re.search(r"^\s+_name\s*=\s*['\"]([^'\"]+)['\"]", block, re.M)
        inherit = re.search(r"^\s+_inherit\s*=\s*(\[[^\]]*\]|['\"][^'\"]*['\"])", block, re.M)
        if name and name.group(1) == model:
            yield "define", begin, block
        elif inherit and re.search(quoted, inherit.group(1)) and not name:
            yield "extend", begin, block


def model_hits(env, model):
    hits = []
    for mod, path in sorted(modules(env).items()):
        for file in py_files(path):
            text = read(file)
            if model in text:
                hits += [(kind, mod, file, line_of(text, begin), begin, block)
                         for kind, begin, block in class_blocks(text, model)]
    return hits


def load_depth(env):
    # dependency depth per module: Odoo loads deeper modules later, so their overrides run first
    paths, memo = modules(env), {}

    def depth(mod, seen=()):
        if mod not in memo:
            try:
                deps = ast.literal_eval(read(os.path.join(paths[mod], "__manifest__.py"))).get("depends", [])
            except (KeyError, ValueError, SyntaxError):
                deps = []
            memo[mod] = 1 + max([depth(d, seen + (mod,)) for d in deps if d in paths and d not in seen] or [-1])
        return memo[mod]
    return depth


def cmd_env(env, _args):
    for key in ("version", "odoo_root", "conf", "conf_source", "db", "python"):
        print("%-11s %s" % (key, env[key]))
    for idx, root in enumerate(env["roots"], 1):
        print("root r%d     %s" % (idx, root))
    for note in env["notes"]:
        print("note        %s" % note)
    print("VERDICT: Odoo %s, %d roots, %d modules" % (env["version"], len(env["roots"]), len(modules(env))))


def cmd_model(env, args):
    hits = model_hits(env, args.model)
    for kind, mod, file, line, _b, _t in hits:
        print("%s:%d %s %s" % (file, line, mod, kind))
    defs = [h for h in hits if h[0] == "define"]
    print("VERDICT: %s %s, %d extensions" % (
        args.model, "defined in %s" % defs[0][1] if defs else "NOT FOUND", len(hits) - len(defs)))


def cmd_field(env, args):
    field_re = re.compile(r"^\s+%s\s*=\s*fields\.(\w+)\(" % re.escape(args.field), re.M)
    count = 0
    for _kind, mod, file, _line, begin, block in model_hits(env, args.model):
        text = read(file)
        for match in field_re.finditer(block):
            snippet = block[match.start():block.find("\n", match.end())].strip()
            print("%s:%d %s %s" % (file, line_of(text, begin + match.start()), mod, snippet[:140]))
            count += 1
    print("VERDICT: %s.%s %d definition(s)" % (args.model, args.field, count))


def cmd_method(env, args):
    def_re = re.compile(r"^([ \t]+)def %s\(" % re.escape(args.method), re.M)
    depth, rows = load_depth(env), []
    for _kind, mod, file, _line, begin, block in model_hits(env, args.model):
        text = read(file)
        for match in def_re.finditer(block):
            indent = len(match.group(1))
            body = []
            for raw in block[match.end():].splitlines()[1:]:
                if raw.strip() and len(raw) - len(raw.lstrip()) <= indent:
                    break
                body.append(raw)
            calls_super = "super(" in "\n".join(body)
            rows.append((depth(mod), mod, file, line_of(text, begin + match.start()), calls_super))
    for idx, (dep, mod, file, line, calls_super) in enumerate(sorted(rows)):
        state = "super" if calls_super else ("NO super: replaces %d lower definition(s)" % idx if idx else "base")
        print("%s:%d %s depth=%d %s" % (file, line, mod, dep, state))
    print("VERDICT: %s.%s %d definition(s); deepest runs first, each super() goes one level down"
          % (args.model, args.method, len(rows)))


def cmd_xmlid(env, args):
    module, _sep, name = args.xmlid.partition(".")
    path = modules(env).get(module)
    if not path or not name:
        die("module %s not found or xmlid not MODULE.NAME" % module)
    pattern = re.compile(r"""id=['"](%s\.)?%s['"]""" % (re.escape(module), re.escape(name)))
    count = 0
    for file in glob.glob(os.path.join(path, "**", "*.xml"), recursive=True):
        for no, line in enumerate(open(file, encoding="utf-8", errors="ignore"), 1):
            if pattern.search(line):
                print("%s:%d %s" % (file, no, line.strip()[:140]))
                count += 1
    print("VERDICT: %s %d hit(s)" % (args.xmlid, count))


def cmd_routes(env, args):
    path = modules(env).get(args.module) or (args.module if os.path.isdir(args.module) else None)
    if not path:
        die("module %s not found" % args.module)
    deco_re = re.compile(r"^([ \t]*)@[\w.]*route\(", re.M)
    count = risky = 0
    for file in py_files(path, skip=("tests", "__pycache__", "static")):
        text = read(file)
        for match in deco_re.finditer(text):
            def_match = re.compile(r"^%sdef (\w+)" % match.group(1), re.M).search(text, match.end())
            if not def_match:
                continue
            deco = text[match.start():def_match.start()]
            nxt = re.compile(r"^%s(?:@|def |class )|^\S" % match.group(1), re.M).search(text, def_match.end())
            body = text[def_match.end():nxt.start() if nxt else len(text)]
            auth = re.search(r"auth\s*=\s*['\"](\w+)", deco)
            auth = auth.group(1) if auth else "user(default)"
            csrf = re.search(r"csrf\s*=\s*(\w+)", deco)
            paths = re.findall(r"['\"](/[^'\"]*)['\"]", deco) or [re.sub(r"\s+", " ", deco.split("(", 1)[1])[:60]]
            sudo = ".sudo(" in body
            flag = " <-- PUBLIC+SUDO: check access as the real user" if auth in ("public", "none") and sudo else ""
            risky += bool(flag)
            print("%s:%d %s auth=%s csrf=%s sudo=%s %s%s" % (
                file, line_of(text, match.start()), def_match.group(1), auth, csrf.group(1) if csrf else "default",
                "yes" if sudo else "no", paths[0], flag))
            count += 1
    print("VERDICT: %s %d route(s), %d public+sudo" % (args.module, count, risky))


# (lo, hi, extensions, regex, hint): the API exists in versions lo..hi; flagged when the source version is
# inside lo..hi and --to is outside. Proof per row: references/versions.md.
MARKERS = [
    (15, 17, "py xml", r"\buser_has_groups\(", "18+: self.env.user.has_groups(spec)"),
    (18, 20, "py", r"\.has_groups\(", "<=17: self.user_has_groups(spec)"),
    (15, 18, "py xml", r"\bgroups_id\b", "19+: res.users.group_ids"),
    (19, 20, "py xml", r"\bgroup_ids\b", "<=18: res.users.groups_id (only if this is res.users)"),
    (19, 20, "py xml", r"\bprivilege_id\b", "<=18: res.groups.category_id"),
    (15, 19, "py", r"\bodoo\.osv\b|from odoo\.osv import", "19+: odoo.fields.Domain; odoo/osv gone in 20"),
    (19, 20, "py", r"from odoo\.fields import[^\n]*\bDomain\b|\bfields\.Domain\b", "<=18: odoo.osv.expression"),
    (15, 18, "py", r"\bself\._(?:cr|uid|context)\b", "19+ deprecated: self.env.cr / env.uid / env.context"),
    (15, 19, "py", r"\bcheck_access_(?:rights|rule)\(", "20: check_access(operation)"),
    (18, 20, "py", r"\.check_access\(", "<=17: check_access_rights + check_access_rule"),
    (15, 17, "py", r"\bname_get\b", "18+: _compute_display_name"),
    (15, 17, "py", r"def _name_search\(", "18+: _search_display_name(operator, value)"),
    (18, 20, "py", r"\b_search_display_name\b", "<=17: _name_search"),
    (16, 20, "py", r"\b_rec_names_search\b", "15: override _name_search"),
    (17, 20, "py", r"\bsearch_fetch\(", "<=16: search() then read()"),
    (17, 20, "py", r"from odoo\.tools(?:\.sql)? import[^\n]*\bSQL\b|\btools\.SQL\(", "<=16: cr.execute(query, params)"),
    (15, 17, "py", r"\bgroup_operator\s*=", "18+: aggregator= (ignored in 20)"),
    (18, 20, "py", r"\baggregator\s*=", "<=17: group_operator="),
    (15, 18, "py", r"\b_sql_constraints\b", "19+: models.Constraint / models.UniqueIndex"),
    (19, 20, "py", r"\bmodels\.(?:Constraint|Index|UniqueIndex)\(", "<=18: _sql_constraints / create_index"),
    (16, 20, "py", r"\bprecompute\s*=", "15: no precompute"),
    (16, 20, "py", r"\bfields\.Json\(", "15: no fields.Json"),
    (16, 20, "py", r"\bindex\s*=\s*['\"](?:btree_not_null|trigram|btree)['\"]", "15: index=True only"),
    (15, 19, "py", r"\.(?:get|set)_param\(", "20: get_str/get_bool/get_int/get_float, set_*"),
    (20, 20, "py", r"\.(?:get|set)_(?:str|bool|int|float)\(", "<=19: get_param / set_param (if ir.config_parameter)"),
    (17, 19, "py", r"\bregistry\.clear_cache\(", "<=16: registry.clear_caches(); 20: env.transaction.invalidate_ormcache()"),
    (15, 18, "py", r"\.clear_caches\(", "17+: registry.clear_cache(name); 20: invalidate_ormcache"),
    (20, 20, "py", r"\binvalidate_ormcache\(", "<=19: registry.clear_cache(name)"),
    (15, 19, "py", r"from odoo\.tools import[^\n]*\bormcache\b|\btools\.ormcache\b", "20: @api.ormcache (old import warns)"),
    (15, 18, "py", r"@api\.returns\b", "19+: removed"),
    (15, 17, "py xml", r"\bnumbercall\b|\bdoall\b", "18+: removed from ir.cron"),
    (18, 18, "py", r"\b_notify_progress\(", "19+: _commit_progress; <=17: none"),
    (19, 20, "py", r"\b_commit_progress\(", "18: _notify_progress; <=17: commit per batch"),
    (15, 17, "py xml", r"\bir\.property\b|\bir_property\b", "18+: company_dependent is a jsonb column, model gone"),
    (15, 18, "py xml", r"\bhr\.contract\b|['\"]hr_contract['\"]", "19+: hr.version in hr (employee.version_id)"),
    (19, 20, "py xml", r"\bhr\.version\b", "<=18: hr.contract (hr_contract)"),
    (15, 16, "py xml js", r"\bmail\.channel\b", "17+: discuss.channel"),
    (17, 20, "py xml js", r"\bdiscuss\.channel\b", "<=16: mail.channel"),
    (15, 16, "py xml", r"\bqty_done\b", "17+: stock.move.line.quantity"),
    (15, 19, "py", r"\b_track_subtype\(|\b_track_template\(", "20: _track_log_get_default_subtype / _track_template_parameters"),
    (15, 16, "py", r"\bSavepointCase\b", "17+: TransactionCase"),
    (15, 19, "py", r"from odoo\.tests\.common import[^\n]*\bForm\b", "20: from odoo.tests import Form (works 15+)"),
    (18, 20, "py", r"^\s+freeze_time\s*=", "<=17: freezegun decorator; 18 string; 19+ odoo.tests freeze_time(...) object"),
    (15, 19, "py", r"\b_check_(?:m2m_)?recursion\(", "18+: _has_cycle() (old removed in 20)"),
    (18, 20, "py", r"\b_has_cycle\(", "<=17: _check_recursion()"),
    (17, 20, "py", r"\b_check_company_domain\b", "<=16: build the company domain by hand"),
    (18, 20, "py", r"\bself\.env\._\(", "<=17: _() from odoo"),
    (16, 20, "py", r"@api\.private\b", "15: none; prefix the method with _"),
    (15, 17, "xml", r"<tree\b", "18+: <list>"),
    (18, 20, "xml", r"<list\b", "<=17: <tree>"),
    (15, 16, "xml", r"\battrs\s*=|\bstates\s*=", "17+: invisible= / readonly= / required= expressions"),
    (16, 20, "xml", r"\bcolumn_invisible\b", "15: invisible=\"1\" on the column"),
    (15, 17, "xml", r"\boe_chatter\b", "18+: <chatter/>"),
    (18, 20, "xml", r"<chatter\b", "<=17: <div class=\"oe_chatter\">"),
    (15, 17, "xml py", r"view_mode[^\n]*\btree\b", "18+: list"),
    (15, 19, "xml", r"\bt-raw\s*=", "20: t-out + Markup (t-raw no longer rendered)"),
    (15, 19, "xml", r"\bt-esc\s*=", "20: t-out (t-esc no longer rendered server-side)"),
    (15, 19, "xml", r"model=['\"]ir\.rule['\"]", "20: ir.access record (operation + domain)"),
    (20, 20, "xml", r"model=['\"]ir\.access['\"]", "<=19: ir.rule + ir.model.access.csv"),
    (15, 16, "js", r"\bodoo\.define\(", "17+: loader remains but legacy widgets are gone: ES module + Owl"),
    (15, 19, "js", r"\buse(?:State|Ref|ExternalListener)\(", "20 Owl 3: proxy() / signal.ref() / useListener()"),
    (20, 20, "js", r"\bproxy\(|\bsignal\.ref\(|\buseListener\(", "<=19 Owl: useState / useRef / useExternalListener"),
]
FILE_MARKERS = [
    (15, 19, "ir.model.access.csv", "20: ir.access.csv (id,name,model_id,group_id/id,operation,domain)"),
    (20, 20, "ir.access.csv", "<=19: ir.model.access.csv"),
]


def port_scan(path, to, src=None):
    hits = []
    manifest = os.path.join(path, "__manifest__.py")
    src = int(src or manifest_major(manifest) or 0) or None
    if src and src != to:
        hits.append((manifest, 1, "manifest %d.0 -> set 'version': '%d.0.x.y.z'" % (src, to)))

    def applies(lo, hi):
        return not lo <= to <= hi and (src is None or lo <= src <= hi)
    compiled = [(lo, hi, exts.split(), re.compile(rx, re.M), hint)
                for lo, hi, exts, rx, hint in MARKERS if applies(lo, hi)]
    for base, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "lib", "node_modules")]
        for name in files:
            file = os.path.join(base, name)
            for lo, hi, fname, hint in FILE_MARKERS:
                if name == fname and applies(lo, hi):
                    hits.append((file, 1, hint))
            ext = name.rsplit(".", 1)[-1]
            active = [m for m in compiled if ext in m[2]]
            if not active:
                continue
            text = read(file)
            for _lo, _hi, _e, rx, hint in active:
                for match in rx.finditer(text):
                    hits.append((file, line_of(text, match.start()), "%s  [%s]" % (hint, match.group(0).strip()[:40])))
    return src, sorted(hits)


def cmd_port_scan(_env, args):
    if not os.path.isfile(os.path.join(args.path, "__manifest__.py")):
        die("%s is not a module directory (no __manifest__.py)" % args.path)
    src, hits = port_scan(args.path, args.to, args.src)
    for file, line, hint in hits:
        print("%s:%d %s" % (file, line, hint))
    print("VERDICT: %s from %s to %d: %d hit(s); each hit needs a fix or a reason, then install + tests on %d"
          % (os.path.basename(os.path.normpath(args.path)), src or "?", args.to, len(hits), args.to))


def write_tree(base, files):
    for rel, body in files.items():
        path = os.path.join(base, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(body)


def selftest_resolve():
    saved_rc = os.environ.pop("ODOO_RC", None)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            src, proj, deb = (os.path.join(tmp, d) for d in ("src", "proj", "deb"))
            write_tree(tmp, {
                "src/odoo-bin": "",
                "src/odoo/release.py": "version_info = (17, 0, 0, 'final', 0, '')\n",
                "src/odoo/addons/base/__manifest__.py": "{'version': '1.3'}",
                "src/addons/sale/__manifest__.py": "{'depends': ['base']}",
                "proj/my_mod/__manifest__.py": "{'version': '17.0.1.0.0', 'depends': ['sale']}",
                "proj/dev.conf": "[options]\naddons_path = %s/addons,%s\ndb_name = demo\n" % (src, proj),
                "proj/.vscode/launch.json": '{\n  // VS Code allows comments\n  "configurations": [{"name": "Odoo",'
                                            ' "program": "${workspaceFolder}/../src/odoo-bin",\n'
                                            '   "args": ["--config=${workspaceFolder}/dev.conf", "-d", "v17"],},]\n}\n',
                "deb/odoo/release.py": "version_info = (18, 0, 0, 'final', 0, '')\n",
                "deb/odoo/addons/base/__manifest__.py": "{'version': '1.3'}",
                "deb/odoo.conf": "[options]\naddons_path = %s/odoo/addons\n" % deb,
            })
            env = resolve(cwd=os.path.join(proj, "my_mod"))
            assert (env["version"], env["odoo_root"], env["db"]) == ("17.0", src, "v17"), env
            assert {"base", "sale", "my_mod"} <= set(modules(env)), modules(env)
            os.remove(os.path.join(proj, ".vscode", "launch.json"))
            env = resolve(cwd=proj)
            assert (env["conf"], env["db"]) == (os.path.join(proj, "dev.conf"), "demo"), env
            os.environ["ODOO_RC"] = os.path.join(deb, "odoo.conf")
            env = resolve(cwd=proj)
            assert (env["version"], env["odoo_root"]) == ("18.0", deb), env
    finally:
        os.environ.pop("ODOO_RC", None)
        if saved_rc is not None:
            os.environ["ODOO_RC"] = saved_rc


def cmd_selftest(_env, _args):
    for lo, hi, exts, rx, hint in MARKERS:
        assert 15 <= lo <= hi <= 20 and exts and hint, rx
        re.compile(rx, re.M)
    selftest_resolve()
    with tempfile.TemporaryDirectory() as tmp:
        write_tree(tmp, {
            "__manifest__.py": "{'name': 'x', 'version': '17.0.1.0.0'}",
            "models/a.py": "class A:\n    def f(self):\n        self.user_has_groups('base.group_user')\n",
            "views/a.xml": "<odoo><tree string='x'/><div class='oe_chatter'/></odoo>",
            "security/ir.model.access.csv": "id\n",
        })
        assert len(port_scan(tmp, 17)[1]) == 0, port_scan(tmp, 17)
        down = port_scan(tmp, 16)[1]
        assert len(down) == 1 and "manifest" in down[0][2], down
        up = " ".join(h[2] for h in port_scan(tmp, 20)[1])
        for expect in ("has_groups", "<list>", "<chatter/>", "ir.access.csv", "manifest"):
            assert expect in up, (expect, up)
        with open(os.path.join(tmp, "models/a.py"), "a") as f:
            f.write("    group_ids = fields.Many2many('res.groups')\n")
        assert not any("group_ids" in h[2] for h in port_scan(tmp, 16, "18")[1])
        assert any("groups_id" in h[2] for h in port_scan(tmp, 18, "19")[1])
    print("VERDICT: selftest ok, %d markers, conf resolution ok" % len(MARKERS))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--conf")
    # --conf also accepted after the subcommand; SUPPRESS keeps a top-level value
    conf = argparse.ArgumentParser(add_help=False)
    conf.add_argument("--conf", default=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("env", parents=[conf])
    sub.add_parser("model", parents=[conf]).add_argument("model")
    for name, extra in (("field", "field"), ("method", "method")):
        p = sub.add_parser(name, parents=[conf])
        p.add_argument("model")
        p.add_argument(extra)
    sub.add_parser("xmlid", parents=[conf]).add_argument("xmlid")
    sub.add_parser("routes", parents=[conf]).add_argument("module")
    p_scan = sub.add_parser("port-scan")
    p_scan.add_argument("path")
    p_scan.add_argument("--to", type=int, required=True)
    p_scan.add_argument("--from", dest="src")
    sub.add_parser("selftest")
    args = parser.parse_args()
    cmds = {"env": cmd_env, "model": cmd_model, "field": cmd_field, "method": cmd_method, "xmlid": cmd_xmlid,
            "routes": cmd_routes, "port-scan": cmd_port_scan, "selftest": cmd_selftest}
    env = resolve(getattr(args, "conf", None)) if args.cmd not in ("port-scan", "selftest") else None
    cmds[args.cmd](env, args)


if __name__ == "__main__":
    main()
