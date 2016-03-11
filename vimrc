" .vimrc heavily stolen from http://dougblack.io/words/a-good-vimrc.html
"
" Enable Pathogen
execute pathogen#infect()

" Colorscheme
set background=dark
colorscheme solarized

" Syntax Processing
syntax enable

" Spaces & Tabs
set tabstop=4           " number of spaces per tab visually displayed
set softtabstop=4       " number of spaces per tab inserted/removed
set expandtab           " tabs are spaces

" UI Config
set number              " show line numbers
set showcmd             " show current command (INSERT/REPLACE/etc)
set cursorline          " highlight current line
filetype indent on      " turn on filetype detection and lang. specific identation
set lazyredraw          " redraw only when neeeded
set showmatch           " highlight matching [{()}]

" Searching
set incsearch           " search as characters are entered
set hlsearch            " highlight matches
" turn off search highlight; default to:  \<space>
nnoremap <leader><space> :nohlsearch<CR>

" Folding
set foldenable          " enable folding
set foldlevelstart=10   " open most folds by default
set foldnestmax=10      " 10 nested fold max
set foldmethod=indent   " fold based on indent level
" space open/closes folds
nnoremap <space> za

" Tmux
" allows cursor change in tmux mode
if exists('$TMUX')
    let &t_SI = "\<Esc>Ptmux;\<Esc>\<Esc>]50;CursorShape=1\x7\<Esc>\\"
    let &t_EI = "\<Esc>Ptmux;\<Esc>\<Esc>]50;CursorShape=0\x7\<Esc>\\"
else
    let &t_SI = "\<Esc>]50;CursorShape=1\x7"
    let &t_EI = "\<Esc>]50;CursorShape=0\x7"
endif

" Autogroups
" This is a slew of commands that create language-specific settings for
" certain filetypes/file extensions. It is important to note they are wrapped
" in an augroup as this ensures the autocmd's are only applied once. In
" addition, the autocmd! directive clears all the autocmd's for the current
" group.
augroup configgroup
    autocmd!
    autocmd VimEnter * highlight clear SignColumn
    autocmd BufWritePre *.php,*.py,*.js,*.txt,*.hs,*.java,*.md
                \:call <SID>StripTrailingWhitespaces()
    autocmd FileType python setlocal commentstring=#\ %s
    autocmd BufEnter Makefile setlocal noexpandtab
    autocmd BufEnter *.sh setlocal tabstop=2
    autocmd BufEnter *.sh setlocal shiftwidth=2
    autocmd BufEnter *.sh setlocal softtabstop=2
augroup END

" Backups
" move backups to /tmp
set backup
set backupdir=~/.vim-tmp,~/.tmp,~/tmp,/var/tmp,/tmp
set backupskip=/tmp/*,/private/tmp/*
set directory=~/.vim-tmp,~/.tmp,~/tmp,/var/tmp,/tmp
set writebackup

" Custom Functions
" strips trailing whitespace at the end of files. this
" is called on buffer write in the autogroup above.
function! <SID>StripTrailingWhitespaces()
    " save last search & cursor position
    let _s=@/
    let l = line(".")
    let c = col(".")
    %s/\s\+$//e
    let @/=_s
    call cursor(l, c)
endfunction

" Errata
set pastetoggle=<F2>    " disable auto-indent when pasting

set laststatus=2        " always display statusline

match ErrorMsg '\s\+$'  " highlight trailing whitespace
