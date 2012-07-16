;;; ipython.el --- Adds support for IPython to python-mode.el

;; Copyright (C) 2002, 2003, 2004, 2005 Alexander Schmolck
;; Author:        Alexander Schmolck
;; Keywords:      ipython python languages oop
;; URL:           http://ipython.org
;; Compatibility: Emacs21, XEmacs21
;; FIXME: #$@! INPUT RING
(defconst ipython-version "0.11"
  "Tied to IPython main version number.")

;;; Commentary
;; This library makes all the functionality python-mode has when running with
;; the normal python-interpreter available for ipython, too. It also enables a
;; persistent py-shell command history across sessions (if you exit python
;; with C-d in py-shell) and defines the command `ipython-to-doctest', which
;; can be used to convert bits of a ipython session into something that can be
;; used for doctests. To install, put this file somewhere in your emacs
;; `load-path' [1] and add the following line to your ~/.emacs file (the first
;; line only needed if the default (``"ipython"``) is wrong or ipython is not 
;; in your `exec-path')::
;;
;;   (setq ipython-command "/SOME-PATH/ipython")
;;   (require 'ipython)
;;
;; Ipython will be set as the default python shell, but only if the ipython
;; executable is in the path. For ipython sessions autocompletion with <tab>
;; is also enabled (experimental feature!). Please also note that all the
;; terminal functions in py-shell are handled by emacs's comint, **not** by
;; (i)python, so importing readline etc. will have 0 effect.
;;
;; To start an interactive ipython session run `py-shell' with ``M-x py-shell``
;; (or the default keybinding ``C-c C-!``).
;;
;; You can customize the arguments passed to the IPython instance at startup by
;; setting the ``py-python-command-args`` variable.  For example, to start
;; always in ``pylab`` mode with hardcoded light-background colors, you can
;; use the following, *after* the ``(require 'ipython)`` line::
;;
;; (setq-default py-python-command-args '("--pylab" "--colors=LightBG"))
;;
;;
;; NOTE: This mode is currently somewhat alpha and although I hope that it
;; will work fine for most cases, doing certain things (like the
;; autocompletion and a decent scheme to switch between python interpreters)
;; properly will also require changes to ipython that will likely have to wait
;; for a larger rewrite scheduled some time in the future.
;;
;;
;; Further note that I don't know whether this runs under windows or not and
;; that if it doesn't I can't really help much, not being afflicted myself.
;;
;;
;; Hints for effective usage
;; -------------------------
;;
;; - IMO the best feature by far of the ipython/emacs combo is how much easier
;;   it makes it to find and fix bugs thanks to the ``%pdb on or %debug``/
;;   pdbtrack combo. **NOTE** for this feature to work, you must turn coloring
;;   off, at least during your debug session.  Type ``%colors nocolor`` before
;;   debugging and file tracking will work, you can re-enable it with ``%colors
;;   linux`` or ``%colors lightbg`` (depending on your preference) when
;;   finished debugging so you can have coloring for the rest of the session.
;;
;;   Try it: first in the ipython to shell do ``%pdb on`` then do something
;;   that will raise an exception (FIXME nice example), or type ``%debug``
;;   after the exception has been raised.  You'll be amazed at how easy it is
;;   to inspect the live objects in each stack frames and to jump to the
;;   corresponding sourcecode locations as you walk up and down the stack trace
;;   (even without ``%pdb on`` you can always use ``C-c -`` (`py-up-exception')
;;   to jump to the corresponding source code locations).
;;
;; - emacs gives you much more powerful commandline editing and output searching
;;   capabilities than ipython-standalone -- isearch is your friend if you
;;   quickly want to print 'DEBUG ...' to stdout out etc.
;;
;; - This is not really specific to ipython, but for more convenient history
;;   access you might want to add something like the following to *the beggining*
;;   of your ``.emacs`` (if you want behavior that's more similar to stand-alone
;;   ipython, you can change ``meta p`` etc. for ``control p``)::
;;
;;         (require 'comint)
;;         (define-key comint-mode-map [(meta p)]
;;           'comint-previous-matching-input-from-input)
;;         (define-key comint-mode-map [(meta n)]
;;           'comint-next-matching-input-from-input)
;;         (define-key comint-mode-map [(control meta n)]
;;            'comint-next-input)
;;         (define-key comint-mode-map [(control meta p)]
;;            'comint-previous-input)
;;
;; - Be aware that if you customize py-python-command previously, this value
;;   will override what ipython.el does (because loading the customization
;;   variables comes later).
;;
;; Please send comments and feedback to the ipython-list
;; (<ipython-user@scipy.org>) where I (a.s.) or someone else will try to
;; answer them (it helps if you specify your emacs version, OS etc;
;; familiarity with <http://www.catb.org/~esr/faqs/smart-questions.html> might
;; speed up things further).
;;
;; Footnotes:
;;
;;     [1] If you don't know what `load-path' is, C-h v load-path will tell
;;     you; if required you can also add a new directory. So assuming that
;;     ipython.el resides in ~/el/, put this in your emacs:
;;
;;
;;           (add-to-list 'load-path "~/el")
;;           (setq ipython-command "/some-path/ipython")
;;           (require 'ipython)
;;
;;
;;
;;
;; TODO:
;;      - do autocompletion properly
;;      - implement a proper switching between python interpreters
;;
;; BUGS:
;;      - neither::
;;
;;         (py-shell "-c print 'FOOBAR'")
;;
;;        nor::
;;
;;         (let ((py-python-command-args (append py-python-command-args
;;                                              '("-c" "print 'FOOBAR'"))))
;;           (py-shell))
;;
;;        seem to print anything as they should
;;
;;      - look into init priority issues with `py-python-command' (if it's set
;;        via custom)


;;; Code
(require 'cl)
(require 'shell)
(require 'executable)
(require 'ansi-color)
;; XXX load python-mode, so that we can screw around with its variables
;; this has the disadvantage that python-mode is loaded even if no
;; python-file is ever edited etc. but it means that `py-shell' works
;; without loading a python-file first. Obviously screwing around with
;; python-mode's variables like this is a mess, but well.
(require 'python-mode)

(defcustom ipython-command "ipython"
  "*Shell command used to start ipython."
  :type 'string
  :group 'python)

;; Users can set this to nil
(defvar py-shell-initial-switch-buffers t
  "If nil, don't switch to the *Python* buffer on the first call to
  `py-shell'.")

(defvar ipython-backup-of-py-python-command nil
  "HACK")


(defvar ipython-de-input-prompt-regexp "\\(?:
In \\[[0-9]+\\]: *.*
----+> \\(.*
\\)[\n]?\\)\\|\\(?:
In \\[[0-9]+\\]: *\\(.*
\\)\\)\\|^[ ]\\{3\\}[.]\\{3,\\}: *\\(.*
\\)"
  "A regular expression to match the IPython input prompt and the python
command after it. The first match group is for a command that is rewritten,
the second for a 'normal' command, and the third for a multiline command.")
(defvar ipython-de-output-prompt-regexp "^Out\\[[0-9]+\\]: "
  "A regular expression to match the output prompt of IPython.")


(if (not (executable-find ipython-command))
    (message (format "Can't find executable %s - ipython.el *NOT* activated!!!"
                     ipython-command))
    ;; change the default value of py-shell-name to ipython
    (setq-default py-shell-name ipython-command)
    ;; turn on ansi colors for ipython and activate completion
    (defun ipython-shell-hook ()
      ;; the following is to synchronize dir-changes
      (make-local-variable 'shell-dirstack)
      (setq shell-dirstack nil)
      (make-local-variable 'shell-last-dir)
      (setq shell-last-dir nil)
      (make-local-variable 'shell-dirtrackp)
      (setq shell-dirtrackp t)
      (add-hook 'comint-input-filter-functions 'shell-directory-tracker nil t)

      (ansi-color-for-comint-mode-on)
      (define-key py-shell-map [tab] 'ipython-complete)
      ;; Add this so that tab-completion works both in X11 frames and inside
      ;; terminals (such as when emacs is called with -nw).
      (define-key py-shell-map "\t" 'ipython-complete)
      ;;XXX this is really just a cheap hack, it only completes symbols in the
      ;;interactive session -- useful nonetheless.
      (define-key py-mode-map [(meta tab)] 'ipython-complete)

      )
    (add-hook 'py-shell-hook 'ipython-shell-hook)
    ;; Regular expression that describes tracebacks for IPython in context and
    ;; verbose mode.

    ;;Adapt python-mode settings for ipython.
    ;; (this works for %xmode 'verbose' or 'context')

    ;; XXX putative regexps for syntax errors; unfortunately the
    ;;     current python-mode traceback-line-re scheme is too primitive,
    ;;     so it's either matching syntax errors, *or* everything else
    ;;     (XXX: should ask Fernando for a change)
    ;;"^   File \"\\(.*?\\)\", line \\([0-9]+\\).*\n.*\n.*\nSyntaxError:"
    ;;^   File \"\\(.*?\\)\", line \\([0-9]+\\)"

    (setq py-traceback-line-re
          "\\(^[^\t >].+?\\.py\\).*\n   +[0-9]+[^\00]*?\n-+> \\([0-9]+\\)+")


    ;; Recognize the ipython pdb, whose prompt is 'ipdb>' or  'ipydb>'
    ;;instead of '(Pdb)'
    (setq py-pdbtrack-input-prompt "\n[(<]*[Ii]?[Pp]y?db[>)]+ ")
    (setq pydb-pydbtrack-input-prompt "\n[(]*ipydb[>)]+ ")

    (setq py-shell-input-prompt-1-regexp "^In \\[[0-9]+\\]: *"
          py-shell-input-prompt-2-regexp "^   [.][.][.]+: *" )
    ;; select a suitable color-scheme
    (unless (delq nil
                  (mapcar (lambda (x) (eq (string-match "^--colors*" x) 0))
                          py-python-command-args))
      (setq-default py-python-command-args
		    (cons (format "--colors=%s"
				  (cond
				   ((eq frame-background-mode 'dark)
				    "Linux")
				   ((eq frame-background-mode 'light)
				    "LightBG")
				   (t ; default (backg-mode isn't always set by XEmacs)
				    "LightBG")))
			  py-python-command-args)))
    (when (boundp 'py-python-command)
      (unless (equal ipython-backup-of-py-python-command py-python-command)
        (setq ipython-backup-of-py-python-command py-python-command)))
    (setq py-python-command ipython-command)
    (when (boundp 'py-shell-name)
      (setq py-shell-name ipython-command)))

;; MODIFY py-shell so that it loads the editing history
(defadvice py-shell (around py-shell-with-history)
  "Add persistent command-history support (in
$PYTHONHISTORY (or \"~/.ipython/history\", if we use IPython)). Also, if
`py-shell-initial-switch-buffers' is nil, it only switches to *Python* if that
buffer already exists."
  (if (comint-check-proc "*Python*")
      ad-do-it
    (setq comint-input-ring-file-name
          (if (string-equal py-python-command ipython-command)
              (concat (or (getenv "IPYTHONDIR") "~/.ipython") "/history")
            (or (getenv "PYTHONHISTORY") "~/.python-history.py")))
    (comint-read-input-ring t)
    (let ((buf (current-buffer)))
      ad-do-it
      (unless py-shell-initial-switch-buffers
        (switch-to-buffer-other-window buf)))))
(ad-activate 'py-shell)
;; (defadvice py-execute-region (before py-execute-buffer-ensure-process)
;;   "HACK: test that ipython is already running before executing something.
;;   Doing this properly seems not worth the bother (unless people actually
;;   request it)."
;; (unless (comint-check-proc "*Python*")
;;     (error "Sorry you have to first do M-x py-shell to send something to ipython.")))
;; (ad-activate 'py-execute-region)

(defadvice py-execute-region (around py-execute-buffer-ensure-process)
  "HACK: if `py-shell' is not active or ASYNC is explicitly desired, fall back
  to python instead of ipython."
  (let ((py-which-shell (if (and (comint-check-proc "*Python*") (not async))
			    py-python-command
			  ipython-backup-of-py-python-command)))
    ad-do-it))
(ad-activate 'py-execute-region)

(defun ipython-to-doctest (start end)
  "Transform a cut-and-pasted bit from an IPython session into something that
looks like it came from a normal interactive python session, so that it can
be used in doctests. Example:


    In [1]: import sys

    In [2]: sys.stdout.write 'Hi!\n'
    ------> sys.stdout.write ('Hi!\n')
    Hi!

    In [3]: 3 + 4
    Out[3]: 7

gets converted to:

    >>> import sys
    >>> sys.stdout.write ('Hi!\n')
    Hi!
    >>> 3 + 4
    7

"
  (interactive "*r\n")
  ;(message (format "###DEBUG s:%de:%d" start end))
  (save-excursion
    (save-match-data
      ;; replace ``In [3]: bla`` with ``>>> bla`` and
      ;;         ``... :   bla`` with ``...    bla``
      (goto-char start)
      (while (re-search-forward ipython-de-input-prompt-regexp end t)
        ;(message "finding 1")
        (cond ((match-string 3)         ;continued
               (replace-match "... \\3" t nil))
              (t
               (replace-match ">>> \\1\\2" t nil))))
      ;; replace ``
      (goto-char start)
      (while (re-search-forward ipython-de-output-prompt-regexp end t)
        (replace-match "" t nil)))))

(defvar ipython-completion-command-string
  "print(';'.join(get_ipython().complete('%s', '%s')[1])) #PYTHON-MODE SILENT\n"
  "The string send to ipython to query for all possible completions")


;; xemacs doesn't have `comint-preoutput-filter-functions' so we'll try the
;; following wonderful hack to work around this case
(if (featurep 'xemacs)
    ;;xemacs
    (defun ipython-complete ()
      "Try to complete the python symbol before point. Only knows about the stuff
in the current *Python* session."
      (interactive)
      (let* ((ugly-return nil)
             (sep ";")
             (python-process (or (get-buffer-process (current-buffer))
                                 ;XXX hack for .py buffers
                                 (get-process py-which-bufname)))
             ;; XXX currently we go backwards to find the beginning of an
             ;; expression part; a more powerful approach in the future might be
             ;; to let ipython have the complete line, so that context can be used
             ;; to do things like filename completion etc.
             (beg (save-excursion (skip-chars-backward "a-z0-9A-Z_." (point-at-bol))
                                  (point)))
             (end (point))
             (pattern (buffer-substring-no-properties beg end))
             (completions nil)
             (completion-table nil)
             completion
             (comint-output-filter-functions
              (append comint-output-filter-functions
                      '(ansi-color-filter-apply
                        (lambda (string)
                                        ;(message (format "DEBUG filtering: %s" string))
                          (setq ugly-return (concat ugly-return string))
                          (delete-region comint-last-output-start
                                         (process-mark (get-buffer-process (current-buffer)))))))))
	;(message (format "#DEBUG pattern: '%s'" pattern))
        (process-send-string python-process
                              (format ipython-completion-command-string pattern))
        (accept-process-output python-process)
	
	;(message (format "DEBUG return: %s" ugly-return))
        (setq completions
              (split-string (substring ugly-return 0 (position ?\n ugly-return)) sep))
        (setq completion-table (loop for str in completions
                                     collect (list str nil)))
        (setq completion (try-completion pattern completion-table))
        (cond ((eq completion t))
              ((null completion)
               (message "Can't find completion for \"%s\"" pattern)
               (ding))
              ((not (string= pattern completion))
               (delete-region beg end)
               (insert completion))
              (t
               (message "Making completion list...")
               (with-output-to-temp-buffer "*Python Completions*"
                 (display-completion-list (all-completions pattern completion-table)))
               (message "Making completion list...%s" "done")))))
  ;; emacs
  (defun ipython-complete ()
    "Try to complete the python symbol before point. Only knows about the stuff
in the current *Python* session."
    (interactive)
    (let* ((ugly-return nil)
           (sep ";")
           (python-process (or (get-buffer-process (current-buffer))
                                        ;XXX hack for .py buffers
                               (get-process py-which-bufname)))
           ;; XXX currently we go backwards to find the beginning of an
           ;; expression part; a more powerful approach in the future might be
           ;; to let ipython have the complete line, so that context can be used
           ;; to do things like filename completion etc.
           (beg (save-excursion (skip-chars-backward "a-z0-9A-Z_./\-" (point-at-bol))
                                (point)))
           (end (point))
	   (line (buffer-substring-no-properties (point-at-bol) end))
           (pattern (buffer-substring-no-properties beg end))
           (completions nil)
           (completion-table nil)
           completion
         (comint-preoutput-filter-functions
          (append comint-preoutput-filter-functions
                  '(ansi-color-filter-apply
                    (lambda (string)
                      (setq ugly-return (concat ugly-return string))
                      "")))))
      (process-send-string python-process
                            (format ipython-completion-command-string pattern line))
      (accept-process-output python-process)
      (setq completions
            (split-string (substring ugly-return 0 (position ?\n ugly-return)) sep))
                                        ;(message (format "DEBUG completions: %S" completions))
      (setq completion-table (loop for str in completions
                                   collect (list str nil)))
      (setq completion (try-completion pattern completion-table))
      (cond ((eq completion t))
            ((null completion)
             (message "Can't find completion for \"%s\" based on line %s" pattern line)
             (ding))
            ((not (string= pattern completion))
             (delete-region (- end (length pattern)) end)
             (insert completion))
            (t
             (message "Making completion list...")
             (with-output-to-temp-buffer "*IPython Completions*"
               (display-completion-list (all-completions pattern completion-table)))
             (message "Making completion list...%s" "done")))))
)

;;; if python-mode's keybinding for the tab key wins then py-shell-complete is called
;;; instead of ipython-complete which result in hanging emacs since there is no shell
;;; process for python-mode to communicate with
(defadvice py-shell-complete
  (around avoid-py-shell-complete activate)
  (ipython-complete))


;;; autoindent support: patch sent in by Jin Liu <m.liu.jin@gmail.com>,
;;; originally written by doxgen@newsmth.net
;;; Minor modifications by fperez for xemacs compatibility.

(defvar ipython-autoindent t
 "If non-nil, enable autoindent for IPython shell through python-mode.")

(defvar ipython-indenting-buffer-name "*IPython Indentation Calculation*"
 "Temporary buffer for indenting multiline statement.")

(defun ipython-get-indenting-buffer ()
 "Return a temporary buffer set in python-mode. Create one if necessary."
 (let ((buf (get-buffer-create ipython-indenting-buffer-name)))
   (set-buffer buf)
   (unless (eq major-mode 'python-mode)
     (python-mode))
   buf))

(defvar ipython-indentation-string nil
 "Indentation for the next line in a multiline statement.")

(defun ipython-send-and-indent ()
 "Send the current line to IPython, and calculate the indentation for
the next line."
 (interactive)
 (if ipython-autoindent
     (let ((line (buffer-substring (point-at-bol) (point)))
           (after-prompt1)
           (after-prompt2))
       (save-excursion
           (comint-bol t)
           (if (looking-at py-shell-input-prompt-1-regexp)
               (setq after-prompt1 t)
             (setq after-prompt2 (looking-at py-shell-input-prompt-2-regexp)))
           (with-current-buffer (ipython-get-indenting-buffer)
             (when after-prompt1
               (erase-buffer))
             (when (or after-prompt1 after-prompt2)
               (delete-region (point-at-bol) (point))
               (insert line)
               (newline-and-indent))))))
 ;; send input line to ipython interpreter
 (comint-send-input))

(defun ipython-indentation-hook (string)
 "Insert indentation string if py-shell-input-prompt-2-regexp
matches last process output."
 (let* ((start-marker (or comint-last-output-start
                          (point-min-marker)))
        (end-marker (process-mark (get-buffer-process (current-buffer))))
        (text (ansi-color-filter-apply (buffer-substring start-marker end-marker))))
   ;; XXX if `text' matches both pattern, it MUST be the last prompt-2
   (when (and (string-match py-shell-input-prompt-2-regexp text)
	      (not (string-match "\n$" text)))
     (with-current-buffer (ipython-get-indenting-buffer)
       (setq ipython-indentation-string
	     (buffer-substring (point-at-bol) (point))))
     (goto-char end-marker)
     (insert ipython-indentation-string)
     (setq ipython-indentation-string nil))))

(add-hook 'py-shell-hook
         (lambda ()
           (add-hook 'comint-output-filter-functions
                     'ipython-indentation-hook)))

(define-key py-shell-map (kbd "RET") 'ipython-send-and-indent)
;;; / end autoindent support

(provide 'ipython)
