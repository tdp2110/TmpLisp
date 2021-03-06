(letrec ((fact (lambda (n)
                 (if (= 0 n)
                     1
                     (* n (fact (- n 1)))
                     )
                 ))
         (mapcar (lambda (f list)
                   (if (null? list)
                       '()
                       (cons (f (car list))
                             (mapcar f (cdr list)))
                       )))
         )
     (mapcar fact '(1 2 3 4 5)))
