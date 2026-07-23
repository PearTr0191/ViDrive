"""Interactive car wizard with input validation and back-navigation."""
from src.config import WIZARD_SEGMENTS
from src.i18n import t
from src.cli import ask, ask_bool


def get_wizard_car() -> dict | None:
    """Run the interactive wizard to create a custom car.

    Supports 'back' to return to the previous question and 'cancel' to abort.
    Returns a car dictionary or None if cancelled.
    """
    print(f"\n{t('wizard_title')}")
    print(t("wizard_instructions"))
    print(t("wizard_nav_hint"))

    data: dict = {}
    questions = [
        ("brand", t("wizard_brand"), None, False),
        ("model", t("wizard_model"), t("wizard_default_model"), False),
        ("price", t("wizard_price"), None, True),
        ("type", t("wizard_type"), t("wizard_default_type"), False),
        ("consumption", t("wizard_consumption"), t("wizard_default_consumption"), True),
        ("annual_maintenance", t("wizard_annual_maint"), t("wizard_default_annual_maint"), True),
        ("seats", t("wizard_seats"), "5", True),
    ]

    idx = 0
    while idx < len(questions):
        key, prompt, default, is_num = questions[idx]

        raw = ask(prompt, default, is_num=is_num)

        if str(raw).strip().lower() == "back":
            if idx > 0:
                idx -= 1
                print(t("wizard_back"))
                continue
            else:
                print(t("wizard_at_first"))
                continue

        if str(raw).strip().lower() == "cancel":
            print(t("wizard_cancelled"))
            return None

        # Validate
        if is_num:
            num = raw if isinstance(raw, (int, float)) else None
            if num is None or (key == "price" and num <= 0) or (key == "seats" and num <= 0):
                print(t("wizard_invalid_num", field=prompt))
                continue
            if key == "seats":
                data[key] = int(num)
            else:
                data[key] = float(num)
        else:
            val = str(raw).strip()
            if not val:
                if default is not None:
                    val = str(default)
                else:
                    print(t("wizard_required", field=prompt))
                    continue
            data[key] = val

        idx += 1

    # Segment selection
    print(f"\n{t('wizard_segments_title')}")
    for i, seg in enumerate(WIZARD_SEGMENTS):
        print(f"    {i+1}. {seg}")
    n_seg = len(WIZARD_SEGMENTS)

    segment_done = False
    while not segment_done:
        seg_choice = ask(t("wizard_segment_prompt", n=n_seg), "1")
        if str(seg_choice).strip().lower() == "back":
            # Go back to the seats question (last question in the list)
            seats_idx = len(questions) - 1
            key, prompt, default, is_num = questions[seats_idx]
            print(t("wizard_back"))
            raw = ask(prompt, default, is_num=is_num)
            if str(raw).strip().lower() == "cancel":
                print(t("wizard_cancelled"))
                return None
            if str(raw).strip().lower() == "back":
                print(t("wizard_at_first"))
                continue
            # Validate and store
            if is_num:
                num = raw if isinstance(raw, (int, float)) else None
                if num is None or (key == "seats" and num <= 0):
                    print(t("wizard_invalid_num", field=prompt))
                    continue
                data[key] = int(num)
            else:
                val = str(raw).strip()
                if not val:
                    if default is not None:
                        val = str(default)
                    else:
                        print(t("wizard_required", field=prompt))
                        continue
                data[key] = val
            # Stay in segment selection loop
            continue

        if str(seg_choice).strip().lower() == "cancel":
            print(t("wizard_cancelled"))
            return None

        if seg_choice is not None and str(seg_choice).isdigit() and 1 <= int(seg_choice) <= n_seg:
            data["segment"] = WIZARD_SEGMENTS[int(seg_choice) - 1]
            segment_done = True
        else:
            print(t("wizard_invalid_range", n=n_seg))

    # Custom depreciation (optional)
    while True:
        depr = ask(t("wizard_depr"), "")
        if depr and str(depr).strip().lower() == "back":
            # Go back to segment selection
            print(t("wizard_back"))
            break  # Exit depreciation loop, re-enter segment selection
        if depr and str(depr).strip().lower() == "cancel":
            print(t("wizard_cancelled"))
            return None
        if depr:
            try:
                data["depreciation_rate"] = float(depr) / 100
            except (ValueError, TypeError):
                data["depreciation_rate"] = None
        else:
            data["depreciation_rate"] = None
        break

    # Normalize type to uppercase
    data["type"] = str(data["type"]).upper()

    return data
