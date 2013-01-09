{#

DO NOT USE THIS AS A BASE WORK,
IF YOU ARE COPY AND PASTING THIS FILE
YOU ARE PROBABLY DOING THINGS WRONG.

Null template, Does nothing except defining a basic structure
To layout the diferents blocks of a notebook.

Subtemplates can Override Blocks to define their custom reresentation.

If one of the block you do overrite is not a leave block, consider
calling super.

{%- block nonLeaveBlock -%}
    #add stuff at beginning
    {{ super() }}
    #add stuff at end
{%- endblock nonLeaveBlock -%}

consider calling super even if block is leave block, we might insert more block later.

#}
{%- block header -%}
{%- endblock header -%}
{%- block body -%}
{%- for worksheet in worksheets -%}
    {%- for cell in worksheet.cells -%}
        {%- block any_cell scoped -%}
            {%- if cell.type in ['code'] -%}
                {%- block codecell scoped -%}
                    {%- block input_group -%}
                        {%- block in_prompt -%}{%- endblock in_prompt -%}
                        {%- block input -%}{%- endblock input -%}
                    {%- endblock input_group -%}
                        {%- if cell.outputs -%}
                    {%- block output_group -%}
                            {%- block output_prompt -%}{%- endblock output_prompt -%}
                            {%- block outputs -%}
                                {%- for output in cell.outputs -%}
                                    {%- if output.output_type in ['pyout'] -%}
                                        {%- block pyout scoped -%}{%- endblock pyout -%}
                                    {%- elif output.output_type in ['stream'] -%}
                                    {%- block stream scoped -%}{%- endblock stream -%}
                                    {%- elif output.output_type in ['display_data'] -%}
                                        {%- block display_data scoped -%}{%- endblock display_data -%}
                                    {%- elif output.output_type in ['pyerr'] -%}
                                        {%- block pyerr scoped -%}
                                        {%- for line in output.traceback -%}
                                            {%- block traceback_line scoped -%}{%- endblock traceback_line -%}
                                        {%- endfor -%}
                                        {%- endblock pyerr -%}
                                    {%- endif -%}
                                {%- endfor -%}
                            {%- endblock outputs -%}
                    {%- endblock output_group -%}
                        {%- endif -%}
                {%- endblock codecell -%}
            {%- elif cell.type in ['markdown'] -%}
                {%- block markdowncell scoped-%}
                {%- endblock markdowncell -%}
            {%- elif cell.type in ['heading'] -%}
                {%- block headingcell scoped-%}
                {%- endblock headingcell -%}
            {%- elif cell.type in ['raw'] -%}
                {%- block rawcell scoped-%}
                {%- endblock rawcell -%}
            {%- else -%}
                {%- block unknowncell scoped-%}
                {%- endblock unknowncell -%}
            {%- endif -%}
        {%- endblock any_cell -%}
    {%- endfor -%}
{%- endfor -%}
{%- endblock body -%}

{%- block footer -%}
{%- endblock footer -%}
