
;; ========== GLOBAL VARIABLES ==========
(setq *tagLoop* "L1")
(setq *tagFloor* "GF")
(setq *tagCount* (if (numberp *tagCount*) *tagCount* 1))

(setq *knownDeviceTypes* '("SD" "MD" "HD" "FIM" "F" "AIM" "AOM" "AVS" "AS"))

;; ========== SetTagBase ==========
(defun c:SetTagBase ( / loop floor)
  (initget 1)
  (setq loop (getstring "\nEnter loop (e.g. L1, L2): "))
  (initget 1)
  (setq floor (getstring "\nEnter floor (e.g. GF, 1F): "))
  (setq *tagLoop* loop)
  (setq *tagFloor* floor)
  (prompt (strcat "\n✔ Tag base updated: " *tagLoop* "/[TYPE]-[COUNT]/" *tagFloor*))
  (princ)
)

;; ========== ResetTagCount ==========
(defun c:ResetTagCount ()
  (setq *tagCount* 1)
  (prompt "\n✔ Tag count reset to 1.")
  (princ)
)

;; ========== SetTagCount ==========
(defun c:SetTagCount ( / newcount)
  (initget 1)
  (setq newcount (getint "\nEnter starting tag number: "))
  (setq *tagCount* newcount)
  (prompt (strcat "\n✔ Tag count manually set to " (itoa *tagCount*) "."))
  (princ)
)

;; ========== Device Type Detection ==========
(defun detect-device-type (blockname)
  (setq upper (strcase blockname))
  (vl-some
    (function (lambda (type)
      (if (wcmatch upper (strcat "*" type "*")) type nil)))
    *knownDeviceTypes*)
)

;; ========== TagDevices ==========
(defun c:TagDevices ( / ss i obj name dev-type tagstr height shiftY minPt maxPt centerX centerY centerZ inspt)
  (vl-load-com)

  (prompt "\nSelect devices to tag:")
  (setq ss (ssget))
  (if ss
    (progn
      (setq i 0)
      (setq height 4.0)
      (setq shiftY 20.0)

      (while (< i (sslength ss))
        (setq obj (vlax-ename->vla-object (ssname ss i)))
        (setq name (vlax-get obj 'EffectiveName))
        (setq dev-type (detect-device-type name))

        (if dev-type
          (progn
            (vla-GetBoundingBox obj 'minPt 'maxPt)
            (setq minPt (vlax-safearray->list minPt))
            (setq maxPt (vlax-safearray->list maxPt))
            (setq centerX (/ (+ (car minPt) (car maxPt)) 2.0))
            (setq centerY (- (/ (+ (cadr minPt) (cadr maxPt)) 2.0) shiftY))
            (setq centerZ (/ (+ (caddr minPt) (caddr maxPt)) 2.0))
            (setq inspt (list centerX centerY centerZ))

            (setq tagstr (strcat *tagLoop* "/" dev-type "-" (itoa *tagCount*) "-" *tagFloor*))

            (entmakex (list
              (cons 0 "MTEXT")
              (cons 100 "AcDbEntity")
              (cons 100 "AcDbMText")
              (cons 10 inspt)
              (cons 40 height)
              (cons 1 tagstr)
              (cons 7 "Standard")
              (cons 71 5)
              (cons 72 5)
            ))

            (setq *tagCount* (1+ *tagCount*))
          )
          (prompt (strcat "\n⚠ Skipped: Unknown device type for "" name ""."))
        )
        (setq i (1+ i))
      )
      (prompt (strcat "\n✔ Tagged " (itoa i) " object(s)."))
    )
    (prompt "\n⚠ No objects selected.")
  )
  (princ)
)
