{#

DO NOT USE THIS AS A BASE,
IF YOU ARE COPY AND PASTING THIS FILE
YOU ARE PROBABLY DOING THINGS INCORRECTLY.

Null template, does nothing except defining a basic structure
To layout the different blocks of a notebook.

Subtemplates can override blocks to define their custom representation.

If one of the block you do overwrite is not a leave block, consider
calling super.

{%- block nonLeaveBlock -%}
    #add stuff at beginning
    {{ super() }}
    #add stuff at end
{%- endblock nonLeaveBlock -%}

consider calling super even if it is a leave block, we might insert more blocks later.

#}
{%- block header -%}
{%- endblock header -%}
{%- block body -%}
{%- for cell in nb.cells -%}
    {%- block any_cell scoped -%}
        {%- if cell.cell_type == 'code' -%}
            {%- block codecell scoped -%}
                {%- block input_group -%}
                    {%- block in_prompt -%}{%- endblock in_prompt -%}
                    {%- block input -%}{%- endblock input -%}
                {%- endblock input_group -%}
                {%- if cell.outputs -%}
                {%- block output_group -%}
                    {%- block output_prompt -%}{%- endblock output_prompt -%}
                    {%- block outputs scoped -%}
                        {%- for output in cell.outputs -%}
                            {%- block output scoped -%}
                                {%- if output.output_type == 'execute_result' -%}
                                    {%- block execute_result scoped -%}{%- endblock execute_result -%}
                                {%- elif output.output_type == 'stream' -%}
                                    {%- block stream scoped -%}
                                        {%- if output.name == 'stdout' -%}
                                            {%- block stream_stdout scoped -%}
                                            {%- endblock stream_stdout -%}
                                        {%- elif output.name == 'stderr' -%}
                                            {%- block stream_stderr scoped -%}
                                            {%- endblock stream_stderr -%}
                                        {%- endif -%}
                                    {%- endblock stream -%}
                                {%- elif output.output_type == 'display_data' -%}
                                    {%- block display_data scoped -%}
                                        {%- block data_priority scoped -%}
                                        {%- endblock data_priority -%}
                                    {%- endblock display_data -%}
                                {%- elif output.output_type == 'error' -%}
                                    {%- block error scoped -%}
                                    {%- for line in output.traceback -%}
                                        {%- block traceback_line scoped -%}{%- endblock traceback_line -%}
                                    {%- endfor -%}
                                    {%- endblock error -%}
                                {%- endif -%}
                            {%- endblock output -%}
                        {%- endfor -%}
                    {%- endblock outputs -%}
                {%- endblock output_group -%}
                {%- endif -%}
            {%- endblock codecell -%}
        {%- elif cell.cell_type in ['markdown'] -%}
            {%- block markdowncell scoped-%}
            {%- endblock markdowncell -%}
        {%- elif cell.cell_type in ['raw'] -%}
            {%- block rawcell scoped -%}
            {%- if cell.metadata.get('raw_mimetype', '').lower() in resources.get('raw_mimetypes', ['']) -%}
            {{ cell.source }}
            {%- endif -%}
            {%- endblock rawcell -%}
        {%- else -%}
            {%- block unknowncell scoped-%}
            {%- endblock unknowncell -%}
        {%- endif -%}
    {%- endblock any_cell -%}
{%- endfor -%}
{%- endblock body -%}

{%- block footer -%}
{%- endblock footer -%}
