# -*- coding: utf-8 -*-
"""English/Arabic strings for the public site.

Only the fixed wording of the site lives here. Anything typed into the admin
panel — job titles and descriptions, client names, brand names, contact
details — is shown exactly as entered, in whatever language it was written.
"""

LANGUAGES = {
    "en": {"name": "English", "dir": "ltr", "switch_to": "العربية"},
    "ar": {"name": "العربية", "dir": "rtl", "switch_to": "English"},
}
DEFAULT_LANG = "en"

TEXT = {
    # --- navigation -------------------------------------------------------
    "nav_services": ("Services", "خدماتنا"),
    "nav_expertise": ("Expertise", "خبراتنا"),
    "nav_work": ("Our Work", "أعمالنا"),
    "nav_why": ("Why Us", "لماذا نحن"),
    "nav_request": ("Request Service", "اطلب الخدمة"),
    "nav_all_work": ("All Work", "كل الأعمال"),

    # --- hero -------------------------------------------------------------
    "hero_kicker": ("Electrical & Automation Specialists · Factories & Production Lines",
                    "متخصصون في الكهرباء والأتمتة · المصانع وخطوط الإنتاج"),
    "hero_title_1": ("Keep Your Production Lines", "حافظ على خطوط إنتاجك"),
    "hero_title_2": ("Running at Full Speed", "تعمل بكامل طاقتها"),
    "hero_sub": (
        "Hands-on troubleshooting, PLC programming, spare parts, and preventive "
        "maintenance for industrial plants — delivered by a team of engineers who "
        "have spent years on the production floor, on equipment from Sidel, Krones, "
        "KHS, SMI and beyond.",
        "تشخيص الأعطال ميدانياً، وبرمجة أنظمة التحكم، وتوريد قطع الغيار، والصيانة "
        "الوقائية للمصانع — يقدمها فريق من المهندسين أمضوا سنوات داخل صالات "
        "الإنتاج، على معدات سيدل وكرونز وKHS وSMI وغيرها."),
    "hero_view_services": ("View Services", "تصفح الخدمات"),

    # --- services ---------------------------------------------------------
    "services_title": ("Services", "خدماتنا"),
    "services_sub": ("Everything your line needs, from emergency callouts to long-term care.",
                     "كل ما يحتاجه خط الإنتاج، من الاستدعاء الطارئ إلى العناية طويلة الأمد."),
    "svc_repair": ("Machine Troubleshooting & Repair", "تشخيص أعطال الماكينات وإصلاحها"),
    "svc_repair_d": (
        "On-site electrical and automation fault finding across production, filling, "
        "and packaging lines. Fast diagnosis, minimal downtime — whatever the brand "
        "of equipment.",
        "تشخيص الأعطال الكهربائية وأعطال الأتمتة في الموقع على خطوط الإنتاج والتعبئة "
        "والتغليف. تشخيص سريع وتقليل زمن التوقف — أياً كانت ماركة المعدات."),
    "svc_plc": ("PLC Programming & Upgrades", "برمجة وتطوير أنظمة التحكم PLC"),
    "svc_plc_d": (
        "Siemens and Allen-Bradley PLC programming, HMI and SCADA development, "
        "control system retrofits, and migration off obsolete hardware.",
        "برمجة أنظمة التحكم سيمنز وألن-برادلي، وتطوير شاشات التشغيل وأنظمة SCADA، "
        "وتحديث أنظمة التحكم، واستبدال الأجهزة المتقادمة."),
    "svc_parts": ("Spare Parts Supply", "توريد قطع الغيار"),
    "svc_parts_d": (
        "Sourcing and supply of genuine and compatible spare parts for industrial "
        "lines — sensors, drives, servo motors, valves, control boards, and "
        "hard-to-find legacy items.",
        "توفير وتوريد قطع الغيار الأصلية والمكافئة للخطوط الصناعية — حساسات، "
        "ودرايفات، وموتورات سيرفو، وصمامات، ولوحات تحكم، وقطع قديمة يصعب إيجادها."),
    "svc_pm": ("Preventive Maintenance Contracts", "عقود الصيانة الوقائية"),
    "svc_pm_d": (
        "Scheduled maintenance programs that maximize line availability, reduce "
        "unplanned stops, and extend the life of your equipment.",
        "برامج صيانة مجدولة ترفع جاهزية الخط، وتقلل التوقفات المفاجئة، وتطيل عمر "
        "المعدات."),
    "svc_training": ("Training & Consultancy", "التدريب والاستشارات"),
    "svc_training_d": (
        "Hands-on training for plant technicians, line and energy audits, spare "
        "parts strategy, and commissioning support for new equipment.",
        "تدريب عملي لفنيي المصنع، ومراجعة أداء الخطوط واستهلاك الطاقة، ووضع خطة "
        "قطع الغيار، ودعم تشغيل المعدات الجديدة."),

    # --- expertise --------------------------------------------------------
    "exp_title": ("Expertise", "خبراتنا"),
    "exp_sub": ("Our team brings deep hands-on experience with the industry's leading "
                "equipment — and the control systems behind all of it.",
                "يمتلك فريقنا خبرة عملية عميقة بأبرز معدات القطاع — وبأنظمة التحكم "
                "التي تقف خلفها جميعاً."),
    "exp_equipment": ("Equipment We Service", "المعدات التي نخدمها"),
    "exp_control": ("Control & Automation Systems", "أنظمة التحكم والأتمتة"),
    "exp_industries": ("Industries Served", "القطاعات التي نخدمها"),
    "exp_note": (
        "We service equipment from these and other manufacturers — tell us what is "
        "on your line. Brand names are shown to indicate the equipment we work on; "
        "we are an independent service provider and are not affiliated with, or "
        "endorsed by, these manufacturers.",
        "نخدم معدات هذه الشركات وغيرها — أخبرنا بما لديك على الخط. تُذكر الأسماء "
        "التجارية للدلالة على المعدات التي نعمل عليها فقط؛ ونحن مزود خدمة مستقل "
        "وغير تابعين لهذه الشركات ولا معتمدين منها."),

    # --- control platforms ------------------------------------------------
    "plat_siemens": ("Siemens S7 / TIA Portal", "سيمنز S7 / TIA Portal"),
    "plat_ab": ("Allen-Bradley / Rockwell", "ألن-برادلي / روكويل"),
    "plat_schneider": ("Schneider Electric", "شنايدر إلكتريك"),
    "plat_hmi": ("HMI & SCADA Systems", "شاشات التشغيل وأنظمة SCADA"),
    "plat_drives": ("VFDs & Servo Drives", "الإنفرترات ودرايفات السيرفو"),
    "plat_networks": ("Profibus / Profinet / Ethernet-IP", "بروفيباس / بروفينت / إيثرنت-IP"),
    "plat_instr": ("Instrumentation & Sensors", "أجهزة القياس والحساسات"),
    "plat_mcc": ("Motor Control Centers (MCC)", "لوحات التحكم بالموتورات (MCC)"),

    # --- industries -------------------------------------------------------
    "ind_beverage": ("Beverage & Bottling", "المشروبات والتعبئة"),
    "ind_food": ("Food Processing", "تصنيع الأغذية"),
    "ind_packaging": ("Packaging & Palletizing", "التغليف والتستيف"),
    "ind_dairy": ("Dairy & Juice", "الألبان والعصائر"),
    "ind_water": ("Water Treatment", "معالجة المياه"),
    "ind_manufacturing": ("General Manufacturing", "الصناعات العامة"),
    "ind_utilities": ("Utilities & Plant Services", "المرافق وخدمات المصانع"),

    # --- our work ---------------------------------------------------------
    "work_title": ("Our Work", "أعمالنا"),
    "work_sub": ("Real jobs on real lines — a sample of what we've delivered.",
                 "أعمال حقيقية على خطوط حقيقية — نماذج مما أنجزناه."),
    "work_more": ("Read more →", "اقرأ المزيد ←"),
    "work_back": ("← Back to our work", "→ العودة إلى أعمالنا"),
    "work_cta": ("Request a Similar Service", "اطلب خدمة مماثلة"),

    # --- clients ----------------------------------------------------------
    "clients_title": ("Clients We Work With", "عملاؤنا"),
    "clients_sub": ("Plants and factories that trust us with their lines.",
                    "مصانع ومنشآت تثق بنا في خطوط إنتاجها."),

    # --- why us -----------------------------------------------------------
    "why_title": ("Why Work With Us", "لماذا تعمل معنا"),
    "why_sub": ("A team of engineers who have run these lines, not just read about them.",
                "فريق من المهندسين شغّلوا هذه الخطوط فعلاً، ولم يقرأوا عنها فقط."),
    "why_1": ("Real Plant Experience", "خبرة ميدانية حقيقية"),
    "why_1_d": ("Not just theory — our engineers have spent years solving live "
                "breakdowns on high-speed production lines under real pressure, "
                "across multiple plants and equipment brands.",
                "ليست نظريات — أمضى مهندسونا سنوات في حل الأعطال المباشرة على خطوط "
                "إنتاج عالية السرعة وتحت ضغط حقيقي، في مصانع متعددة وعلى ماركات "
                "معدات مختلفة."),
    "why_2": ("Downtime Is the Enemy", "التوقف هو العدو"),
    "why_2_d": ("Fast response and structured fault-finding to get your line back up "
                "in hours, not days.",
                "استجابة سريعة وتشخيص منهجي لإعادة تشغيل خطك خلال ساعات، لا أيام."),
    "why_3": ("Honest, Practical Advice", "نصيحة صادقة وعملية"),
    "why_3_d": ("Clear recommendations on repairs, parts, and upgrades — only what "
                "your plant actually needs.",
                "توصيات واضحة بشأن الإصلاحات وقطع الغيار والتحديثات — وما يحتاجه "
                "مصنعك فعلاً فقط."),
    "why_4": ("A Team, Not One Person", "فريق عمل، لا شخص واحد"),
    "why_4_d": ("Electrical, automation, and mechanical skills under one roof — so we "
                "can cover a full line and respond even when one engineer is already "
                "on site elsewhere.",
                "خبرات كهربائية وأتمتة وميكانيكية تحت مظلة واحدة — لنغطي الخط بالكامل "
                "ونستجيب حتى لو كان أحد المهندسين في موقع آخر."),

    # --- contact form -----------------------------------------------------
    "contact_title": ("Request a Service", "اطلب الخدمة"),
    "contact_sub": ("Tell us about your machine and the problem. We'll get back to you "
                    "quickly with next steps and availability.",
                    "أخبرنا عن ماكينتك والمشكلة. سنعاود التواصل معك سريعاً بالخطوات "
                    "التالية ومواعيد التوفر."),
    "form_name": ("Your Name", "الاسم"),
    "form_company": ("Company", "الشركة"),
    "form_phone": ("Phone / WhatsApp", "الهاتف / واتساب"),
    "form_phone_hint": ("Pick your country, then your number without the leading 0.",
                        "اختر دولتك، ثم أدخل رقمك بدون الصفر في البداية."),
    "form_email": ("Email", "البريد الإلكتروني"),
    "form_machine": ("Machine / Line", "الماكينة / الخط"),
    "form_machine_ph": ("e.g. Krones filler, KHS packer, SMI wrapper",
                        "مثال: فيلر كرونز، باكر KHS، رابر SMI"),
    "form_service": ("Service Needed", "الخدمة المطلوبة"),
    "form_other": ("Other", "أخرى"),
    "form_message": ("Describe the problem or request", "اشرح المشكلة أو الطلب"),
    "form_message_ph": ("What is happening on the machine? Any alarm codes?",
                        "ما الذي يحدث في الماكينة؟ هل هناك أكواد أعطال؟"),
    "form_submit": ("Send Request", "إرسال الطلب"),
    "form_sent": ("Your request has been received. We'll contact you as soon as possible.",
                  "تم استلام طلبك. سنتواصل معك في أقرب وقت ممكن."),
    "country_label": ("Country code", "رمز الدولة"),

    # --- footer -----------------------------------------------------------
    "footer_staff": ("Staff login", "دخول الموظفين"),
    "not_found_title": ("Page Not Found", "الصفحة غير موجودة"),
    "not_found_sub": ("That job is no longer published, or the link is wrong.",
                      "هذا العمل لم يعد منشوراً، أو الرابط غير صحيح."),
    "not_found_cta": ("Go to the website", "الذهاب إلى الموقع"),
    "offline_title": ("No Connection", "لا يوجد اتصال"),
}


def translate(key, lang):
    """Look up a string. Falls back to English, then to the key itself."""
    pair = TEXT.get(key)
    if pair is None:
        return key
    return pair[1] if lang == "ar" and pair[1] else pair[0]
