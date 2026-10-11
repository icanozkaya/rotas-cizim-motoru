(defun c:TotLen ( / sel i en len total insPt unitCode unitName)
  (setq unitCode (getvar "INSUNITS"))
  (setq unitName
    (cond
      ((= unitCode 4) "Millimeters")
      ((= unitCode 6) "Meters")
      ((= unitCode 2) "Feet")
      ((= unitCode 1) "Inches")
      (T "Units")
    )
  )

  (setq sel (ssget '((0 . "*LINE,ARC,LWPOLYLINE,POLYLINE,SPLINE"))))
  (if sel
    (progn
      (setq i 0 total 0.0)
      (while (< i (sslength sel))
        (setq en (vlax-ename->vla-object (ssname sel i)))
        (if (vlax-property-available-p en 'Length)
          (setq total (+ total (vlax-get en 'Length)))
        )
        (setq i (1+ i))
      )

      ;; if INSUNITS=mm but values look like meters, scale up
      (if (and (= unitCode 4) (< total 1000.0))
        (progn
          (setq total (* total 1000.0)) ; assume meters → mm
        )
      )

      (princ (strcat "\nTotal length = " (rtos total 2 2) " " unitName))
      (setq insPt (getpoint "\nPick point to place total length text: "))
      (entmakex
        (list
          (cons 0 "MTEXT")
          (cons 100 "AcDbEntity")
          (cons 100 "AcDbMText")
          (cons 10 insPt)
          (cons 40 (getvar "TEXTSIZE"))
          (cons 1 (strcat "Total length = " (rtos total 2 2) " " unitName))
          (cons 7 "Standard")
          (cons 71 1)
          (cons 72 5)
        )
      )
    )
    (princ "\nNo valid objects selected.")
  )
  (princ)
)
