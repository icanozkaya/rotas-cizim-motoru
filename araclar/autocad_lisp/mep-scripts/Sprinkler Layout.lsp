(defun c:SprinklerLayout ( / insPt width length Lmax Smax sprinklerBlock y i j xPoints x yTop)

  ;; Get user inputs
  (setq insPt (getpoint "\nPick insertion point (bottom-left corner): "))
  (setq width (getreal "\nEnter bay WIDTH (Y direction): "))
  (setq length (getreal "\nEnter bay LENGTH (X direction): "))
  (setq Lmax (getreal "\nEnter sprinkler branch spacing (Y direction - Lmax): "))
  (setq Smax (getreal "\nEnter sprinkler head spacing (X direction - Smax): "))
  (setq sprinklerBlock (getstring T "\nEnter sprinkler BLOCK name: "))

  ;; Start Y position from bottom
  (setq y (cadr insPt))

  (while (<= y (+ (cadr insPt) width))
    ;; Start X position for this branch
    (setq x (car insPt))
    (setq xPoints '())

    (while (<= x (+ (car insPt) length))
      ;; Insert sprinkler block
      (command "._-insert" sprinklerBlock (list x y 0.0) 1 1 0)
      ;; Collect point
      (setq xPoints (append xPoints (list (list x y 0.0))))
      ;; Move to next sprinkler position
      (setq x (+ x Smax))
    )

    ;; Draw line only if there are at least 2 points
    (if (and xPoints (cdr xPoints))
      (entmakex
        (list
          '(0 . "LINE")
          (cons 10 (car xPoints))
          (cons 11 (last xPoints))
          (cons 62 7) ;; optional: color
        )
      )
    )

    ;; Move to next branch line
    (setq y (+ y Lmax))
  )

  (princ "\n✅ Sprinklers placed with exact spacing and branch lines.")
  (princ)
)
