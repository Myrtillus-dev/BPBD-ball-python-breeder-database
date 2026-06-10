"""
sync.py — Centralized data synchronization between database tables.

WHY THIS EXISTS:
  The app stores related data in separate tables. When data changes in one
  table, related tables need to be updated automatically so the user never
  has to enter the same information twice.

  All sync rules live here in one place. If you need to add or change a
  sync rule, this is the only file you need to edit.

SYNC RULES:
  after_husbandry_save(data)
    → Weight Check event: copies weight_g to animals.weight_g
      So the animal profile always shows the latest measured weight.
    → Feeding event: no direct field sync, but dashboard alerts update.

  after_hatchling_save(data)
    → Status = Holdback: creates or updates an Animal Profile with:
        ID (= hatchling ID), name (= hatchling ID, breeder can rename),
        morph, het, sex, dob (= hatch_date), birth weight, sire_id, dam_id
      Returns True if a NEW animal was created, False if updated existing.
    → Other statuses: no action.

  after_clutch_save(data)
    → If hatch_date_actual is set: copies it to hatch_date of all
      hatchlings in this clutch that don't yet have a hatch_date.
      Also updates dob in animals if the hatchling is a holdback animal.

SAFETY:
  All sync functions catch exceptions and log them silently.
  A sync failure never prevents the original save from completing.
"""

import database as db


def after_husbandry_save(data: dict):
    """
    Sync husbandry data to related tables after a log entry is saved.

    Weight Check → animals.weight_g:
      Updates the animal's current weight with the newly logged value.
      All other animal fields are preserved (no data loss).
    """
    animal_id  = data.get("animal_id")
    event_type = data.get("event_type")
    weight     = data.get("weight_g")

    if not animal_id:
        return

    if event_type == "Weight Check" and weight:
        animal = db.get_animal(animal_id)
        if not animal:
            return
        try:
            # Build full update dict preserving all existing fields
            # Only weight_g is changed — nothing else is overwritten
            update = {k: animal[k] for k in animal.keys()}
            update["weight_g"] = float(str(weight))
            db.save_animal(update, is_new=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "after_husbandry_save weight sync failed: %s", e)


def after_hatchling_save(data: dict) -> bool:
    """
    Sync hatchling data to Animal Profiles when status is Holdback.

    Returns True  → new Animal Profile was created
    Returns False → existing profile updated, or status is not Holdback
    """
    if data.get("status") != "Holdback":
        return False
    hid = data.get("id")
    if not hid:
        return False
    return _sync_holdback_to_animals(data)


def _sync_holdback_to_animals(data: dict) -> bool:
    """
    Create or update an Animal Profile from hatchling holdback data.

    NEW animal (profile doesn't exist yet):
      Creates a complete profile with all available hatchling data.
      Name defaults to the hatchling ID — breeder renames in Animals tab.

    EXISTING animal (profile already exists):
      Only fills in fields that are currently empty/None in the profile.
      Never overwrites data the breeder has already entered manually.
      Returns False (not newly created).
    """
    hid      = data["id"]
    existing = db.get_animal(hid)

    # Build morph string from confirmed + possible morph
    morph = " ".join(filter(None, [
        data.get("confirmed_morph"),
        data.get("possible_morph"),
    ]))

    if existing:
        # Animal profile already exists — only update empty fields
        updates = {k: existing[k] for k in existing.keys()}

        # Update morph only if not already set
        if data.get("confirmed_morph") and not existing["morph"]:
            updates["morph"] = morph or None
        # Update het only if not already set
        if data.get("het_genes") and not existing["het"]:
            updates["het"] = data["het_genes"]
        # Update sex only if currently unknown or empty
        if data.get("sex") and (not existing["sex"] or existing["sex"] == "Unknown"):
            updates["sex"] = data["sex"]
        # Update weight only if not already set
        if data.get("birth_weight_g") and not existing["weight_g"]:
            try:
                updates["weight_g"] = float(str(data["birth_weight_g"]))
            except ValueError:
                pass

        try:
            db.save_animal(updates, is_new=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "_sync_holdback_to_animals update failed: %s", e)
        return False  # Existing profile, not newly created

    else:
        # No profile exists — create one from hatchling data
        try:
            db.save_animal({
                "id":          hid,
                "name":        hid,    # Breeder should rename in Animals tab
                "sex":         data.get("sex") or "Unknown",
                "dob":         data.get("hatch_date"),
                "morph":       morph or None,
                "het":         data.get("het_genes"),
                "weight_g":    _safe_float(data.get("birth_weight_g")),
                "sire_id":     data.get("sire_id"),
                "dam_id":      data.get("dam_id"),
                "status":      "Active",
                "feed_interval": 7,
                "notes": f"Holdback from clutch {data.get('clutch_id', '')}",
            }, is_new=True)
            return True  # New profile created
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "_sync_holdback_to_animals create failed: %s", e)
            return False


def after_clutch_save(data: dict):
    """
    Propagate clutch hatch date to hatchlings after a clutch is saved.

    If hatch_date_actual is set on the clutch:
      - Updates hatch_date on all hatchlings of this clutch that have
        no hatch_date yet (does not overwrite manually entered dates).
      - Also updates dob in the Animal Profile if that hatchling is
        a holdback animal with no dob set yet.
    """
    cid        = data.get("id")
    hatch_date = data.get("hatch_date_actual")
    if not cid or not hatch_date:
        return

    hatchlings = db.get_hatchlings(cid)
    for h in hatchlings:
        if h["hatch_date"]:
            continue  # Already has a date — don't overwrite

        try:
            # Update hatchling's hatch_date
            db.execute(
                "UPDATE hatchlings SET hatch_date=? WHERE id=?",
                (hatch_date, h["id"]))

            # If this hatchling is a holdback animal, also set dob
            a = db.get_animal(h["id"])
            if a and not a["dob"]:
                db.execute(
                    "UPDATE animals SET dob=? WHERE id=?",
                    (hatch_date, h["id"]))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                "after_clutch_save hatch_date sync failed for %s: %s",
                h["id"], e)


def _safe_float(val):
    """Convert val to float, return None if conversion fails."""
    if val is None:
        return None
    try:
        return float(str(val))
    except (ValueError, TypeError):
        return None
